from sqlalchemy.orm import Session

from app.repositories.knowledge import KnowledgeRepository
from app.schemas.classification import ClassificationResult
from app.schemas.guidance import Citation
from app.schemas.incident import IncidentData
from app.services.ai.base import EmbeddingProvider
from app.services.classification.taxonomy import label
from app.services.rag.sanitize import safe_attr, strip_injections


class Retriever:
    def __init__(self, db: Session, embeddings: EmbeddingProvider, top_k: int = 5, min_score: float = 0.05) -> None:
        self.repo = KnowledgeRepository(db)
        self.embeddings = embeddings
        self.top_k, self.min_score = top_k, min_score

    def search(self, query: str, top_k: int | None = None, category: str | None = None) -> list[Citation]:
        [vector] = self.embeddings.embed([query])
        hits = self.repo.search(vector, top_k or self.top_k, category)
        out: list[Citation] = []
        for h in hits:
            if h.score < self.min_score:
                continue
            excerpt, _ = strip_injections(h.chunk.content)  # defence in depth at query time
            out.append(Citation(
                id=f"S{len(out) + 1}",
                title=safe_attr(h.document.title),
                organization=safe_attr(h.document.organization),
                url=safe_attr(h.document.url),
                category=h.document.category,
                document_type=h.document.document_type,
                published_date=h.document.published_date,
                score=round(h.score, 4),
                excerpt=excerpt,
            ))
        return out

    def for_incident(self, incident: IncidentData, classification: ClassificationResult) -> list[Citation]:
        """Topic retrieval plus one reporting/evidence chunk so guidance can cite real channels."""
        topic = f"{label(classification.category)} {classification.subtype or ''} {incident.platform or ''} {incident.description[:500]}"
        results = self.search(topic, top_k=self.top_k)
        need = "how to report cybercrime helpline portal" + (" bank unauthorised transaction" if incident.financial_loss else "")
        for extra in self.search(need, top_k=2):
            if all(extra.excerpt != r.excerpt for r in results):
                results.append(extra)
        for i, r in enumerate(results, 1):
            r.id = f"S{i}"
        return results
