from abc import ABC, abstractmethod
from typing import Any


class LLMError(Exception):
    """Provider/transport failure (network, auth, rate limit)."""


class StructuredOutputError(Exception):
    """The model did not return valid output for the requested schema."""


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, *, task: str, system: str, user: str, json_schema: dict[str, Any] | None = None) -> str:
        """Return raw text. When json_schema is given the text should be a JSON object.

        `task` identifies the prompt (extraction, classification, ...) for logging and the mock.
        """


class EmbeddingProvider(ABC):
    name: str = "base"
    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...
