from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.services.ai.base import EmbeddingProvider, LLMProvider
from app.services.ai.factory import get_embeddings, get_llm
from app.services.pipeline import Pipeline


def get_pipeline(
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
    embeddings: EmbeddingProvider = Depends(get_embeddings),
    settings: Settings = Depends(get_settings),
) -> Pipeline:
    return Pipeline(db, llm, embeddings, settings)
