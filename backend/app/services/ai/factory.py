from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.ai.base import EmbeddingProvider, LLMProvider


def build_llm(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "mock":
        from app.services.ai.providers.mock import MockLLM

        return MockLLM()
    if provider == "openai":
        from app.services.ai.providers.openai_compat import OpenAICompatibleLLM

        return OpenAICompatibleLLM(settings.llm_base_url, settings.llm_api_key, settings.llm_model,
                                   settings.llm_temperature, settings.llm_timeout_seconds)
    if provider == "anthropic":
        from app.services.ai.providers.anthropic import AnthropicLLM

        return AnthropicLLM(settings.llm_api_key, settings.llm_model, settings.llm_temperature,
                            settings.llm_timeout_seconds, settings.llm_base_url)
    raise ValueError(f"Unsupported LLM_PROVIDER={settings.llm_provider!r} (use mock|openai|anthropic)")


def build_embeddings(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider == "hash":
        from app.services.ai.providers.hash_embeddings import HashEmbeddings

        return HashEmbeddings(settings.embedding_dim)
    if provider == "openai":
        from app.services.ai.providers.openai_compat import OpenAICompatibleEmbeddings

        return OpenAICompatibleEmbeddings(settings.embedding_base_url, settings.embedding_api_key,
                                          settings.embedding_model, settings.embedding_dim)
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER={settings.embedding_provider!r} (use hash|openai)")


@lru_cache
def get_llm() -> LLMProvider:
    return build_llm(get_settings())


@lru_cache
def get_embeddings() -> EmbeddingProvider:
    return build_embeddings(get_settings())
