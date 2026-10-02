"""Integration tests against a real PostgreSQL + pgvector database.

Run:  TEST_DATABASE_URL=postgresql+psycopg://cyber:<pw>@localhost:5433/cyberassist_test pytest tests/postgres
The database is reset (downgrade to base, upgrade to head) — never point this at real data.
"""
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.services.ai.providers.hash_embeddings import HashEmbeddings
from app.services.ai.providers.mock import MockLLM
from app.services.conversation.orchestrator import Orchestrator
from app.repositories.conversations import ConversationRepository
from app.schemas.conversation import MessageIn
from app.services.pipeline import Pipeline
from app.services.rag.ingest import Ingestor
from tests.conftest import BACKEND, DEMO, KB_DIR

URL = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(not URL.startswith("postgresql"), reason="TEST_DATABASE_URL (PostgreSQL) not set"),
]


@pytest.fixture(scope="module")
def pg_session_factory():
    engine = create_engine(URL)
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, "base")
        command.upgrade(cfg, "head")
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        Ingestor(db, HashEmbeddings(384)).ingest_dir(Path(KB_DIR))
    yield factory
    engine.dispose()


def test_pgvector_schema(pg_session_factory):
    with pg_session_factory() as db:
        assert db.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar()
        col = db.execute(text(
            "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
            "WHERE attrelid='knowledge_chunks'::regclass AND attname='embedding'")).scalar()
        assert col == "vector(384)"
        idx = db.execute(text("SELECT indexdef FROM pg_indexes WHERE indexname='ix_knowledge_chunks_embedding'")).scalar()
        assert "hnsw" in idx and "vector_cosine_ops" in idx
        assert db.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"


def test_embeddings_stored_as_vectors(pg_session_factory):
    with pg_session_factory() as db:
        n, dims, norm = db.execute(text(
            "SELECT count(*), min(vector_dims(embedding)), avg(vector_norm(embedding)) FROM knowledge_chunks")).one()
        assert n > 10 and dims == 384 and abs(norm - 1.0) < 1e-3


def test_cosine_search_uses_pgvector(pg_session_factory):
    with pg_session_factory() as db:
        p = Pipeline(db, MockLLM(), HashEmbeddings(384), get_settings())
        assert db.get_bind().dialect.name == "postgresql"
        hits = p.retriever.search("UPI PIN collect request QR code receive money", top_k=3)
        assert hits and hits[0].category == "upi_fraud"
        assert len({h.title for h in hits}) == len(hits)  # one citation per document
        assert all(h.source_note for h in hits)


def test_embedding_mismatch_is_refused(pg_session_factory):
    from app.core.errors import AppError

    class Other(HashEmbeddings):
        model_name = "other"

    with pg_session_factory() as db:
        p = Pipeline(db, MockLLM(), Other(384), get_settings())
        with pytest.raises(AppError):
            p.retriever.search("UPI")


def test_demo_conversation_persists_in_postgres(pg_session_factory):
    with pg_session_factory() as db:
        p = Pipeline(db, MockLLM(), HashEmbeddings(384), get_settings())
        conv = ConversationRepository(db).create()
        result = Orchestrator(db, p).handle(conv.id, MessageIn(content=DEMO))
        assert result.classification and result.classification.category == "phishing"
        assert result.sources
        rows = db.execute(text("SELECT count(*) FROM messages WHERE conversation_id=:c"), {"c": conv.id}).scalar()
        assert rows == 2
        assert db.execute(text("SELECT count(*) FROM evidence_items WHERE incident_id=:i"), {"i": result.incident_id}).scalar() > 0
