"""Anthropic Messages API provider (plain HTTP)."""
import json
from typing import Any

import httpx

from app.services.ai.base import LLMError, LLMProvider


class AnthropicLLM(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, temperature: float, timeout: float,
                 base_url: str = "https://api.anthropic.com/v1") -> None:
        self.model, self.temperature = model, temperature
        self.base_url = base_url.rstrip("/") if "anthropic" in base_url else "https://api.anthropic.com/v1"
        self.client = httpx.Client(
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}, timeout=timeout
        )

    def complete(self, *, task: str, system: str, user: str, json_schema: dict[str, Any] | None = None) -> str:
        if json_schema is not None:
            system = f"{system}\n\nRespond with ONLY a JSON object matching this JSON Schema:\n{json.dumps(json_schema)}"
        body = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": self.temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        try:
            resp = self.client.post(f"{self.base_url}/messages", json=body)
            resp.raise_for_status()
            return "".join(b.get("text", "") for b in resp.json()["content"] if b.get("type") == "text")
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise LLMError(f"{task}: LLM request failed ({type(exc).__name__})") from exc
