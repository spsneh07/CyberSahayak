"""OpenAI-compatible chat + embeddings (OpenAI, Groq, OpenRouter, Ollama, LM Studio...)."""
import json
import logging
import time
from typing import Any

import httpx

from app.core.logging import redact
from app.services.ai.base import EmbeddingProvider, LLMError, LLMProvider


log = logging.getLogger(__name__)
RETRY_STATUS = {429, 500, 502, 503, 504}


def post_with_retry(client: httpx.Client, url: str, body: dict[str, Any], attempts: int = 4) -> httpx.Response:
    """POST with bounded exponential backoff on rate limits / transient server errors."""
    for attempt in range(attempts):
        resp = client.post(url, json=body)
        if resp.status_code not in RETRY_STATUS or attempt == attempts - 1:
            return resp
        try:
            wait = min(float(resp.headers.get("retry-after", 2 ** attempt)), 20.0)
        except ValueError:
            wait = float(2 ** attempt)
        log.warning("provider returned %s; retrying in %.1fs", resp.status_code, wait)
        time.sleep(wait)
    return resp


def describe_error(exc: Exception) -> str:
    """Status code + provider error message (redacted, truncated) — never the request headers."""
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            detail = exc.response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = exc.response.text
        return f"HTTP {exc.response.status_code}: {redact(str(detail))[:200]}"
    return type(exc).__name__


class OpenAICompatibleLLM(LLMProvider):
    name = "openai"

    def __init__(self, base_url: str, api_key: str, model: str, temperature: float, timeout: float) -> None:
        self.base_url, self.model, self.temperature = base_url.rstrip("/"), model, temperature
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.client = httpx.Client(headers=headers, timeout=timeout)

    def complete(self, *, task: str, system: str, user: str, json_schema: dict[str, Any] | None = None) -> str:
        if json_schema is not None:
            system = f"{system}\n\nRespond with ONLY a JSON object matching this JSON Schema:\n{json.dumps(json_schema)}"
        body: dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if json_schema is not None:
            body["response_format"] = {"type": "json_object"}
        try:
            resp = post_with_retry(self.client, f"{self.base_url}/chat/completions", body)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"] or ""
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMError(f"{task}: LLM request failed ({describe_error(exc)})") from exc


class OpenAICompatibleEmbeddings(EmbeddingProvider):
    name = "openai"

    def __init__(self, base_url: str, api_key: str, model: str, dim: int, timeout: float = 60) -> None:
        self.base_url, self.model, self.dim = base_url.rstrip("/"), model, dim
        self.model_name = model
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.client = httpx.Client(headers=headers, timeout=timeout)

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 64):
            batch = texts[i : i + 64]
            try:
                resp = post_with_retry(self.client, f"{self.base_url}/embeddings",
                                       {"model": self.model, "input": batch, "dimensions": self.dim})
                resp.raise_for_status()
                data = sorted(resp.json()["data"], key=lambda d: d["index"])
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                raise LLMError(f"embedding request failed ({describe_error(exc)})") from exc
            for d in data:
                if len(d["embedding"]) != self.dim:
                    raise LLMError(f"embedding dim {len(d['embedding'])} != EMBEDDING_DIM {self.dim}")
                out.append(d["embedding"])
        return out
