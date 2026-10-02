from fastapi import APIRouter, Depends

from app.api.deps import get_pipeline
from app.schemas.guidance import Citation, RagSearchRequest
from app.services.pipeline import Pipeline

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search", response_model=list[Citation])
def search(body: RagSearchRequest, p: Pipeline = Depends(get_pipeline)) -> list[Citation]:
    return p.retriever.search(body.query, top_k=body.top_k, category=body.category)
