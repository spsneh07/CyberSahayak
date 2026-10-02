"""Semantic embeddings computed locally with sentence-transformers (no API key).

Default model: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions), downloaded
from Hugging Face on first use and cached. Requires `pip install -r requirements-ml.txt`.
"""
from app.services.ai.base import EmbeddingProvider, LLMError


class LocalSentenceEmbeddings(EmbeddingProvider):
    name = "local"

    def __init__(self, model: str, dim: int) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # optional dependency
            raise LLMError("EMBEDDING_PROVIDER=local needs `pip install -r requirements-ml.txt`") from exc
        self.model_name = model
        self.model = SentenceTransformer(model, device="cpu")
        self.dim = dim
        get_dim = getattr(self.model, "get_embedding_dimension", None) or self.model.get_sentence_embedding_dimension
        actual = get_dim()
        if actual != dim:
            raise LLMError(f"model {model} produces {actual}-d vectors but EMBEDDING_DIM={dim}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vectors]
