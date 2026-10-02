"""Structured LLM output: request JSON for a Pydantic schema, parse, validate, repair once."""
import json
import logging
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.services.ai.base import LLMProvider, StructuredOutputError
from app.services.language import LOCALISED_TASKS, language_instruction

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def parse_json_object(text: str) -> dict:
    """Parse a JSON object from model text, tolerating code fences and leading/trailing prose."""
    cleaned = _FENCE.sub("", text.strip())
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise
        value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise json.JSONDecodeError("expected a JSON object", cleaned, 0)
    return value


def generate_structured(llm: LLMProvider, *, task: str, system: str, user: str,
                        schema: type[T], max_attempts: int = 2) -> T:
    json_schema = schema.model_json_schema()
    if task in LOCALISED_TASKS:
        system += language_instruction()
    prompt = user
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        raw = llm.complete(task=task, system=system, user=prompt, json_schema=json_schema)
        try:
            return schema.model_validate(parse_json_object(raw))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)[:800]
            log.warning("structured output invalid task=%s attempt=%d: %s", task, attempt, type(exc).__name__)
            prompt = (
                f"{user}\n\nYour previous reply was not valid for the required schema.\n"
                f"Error: {last_error}\nReturn ONLY the corrected JSON object."
            )
    raise StructuredOutputError(f"{task}: invalid structured output after {max_attempts} attempts: {last_error}")
