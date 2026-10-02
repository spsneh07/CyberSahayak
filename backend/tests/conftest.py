"""Test setup: throwaway SQLite DB migrated with Alembic, mock LLM, hash embeddings, real KB ingestion."""
import os
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="cyberassist-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP, 'test.db').as_posix()}"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "hash"
os.environ["EMBEDDING_DIM"] = "384"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.services.ai.factory import get_embeddings, get_llm  # noqa: E402
from app.services.ai.providers.hash_embeddings import HashEmbeddings  # noqa: E402
from app.services.ai.providers.mock import MockLLM  # noqa: E402
from app.services.pipeline import Pipeline  # noqa: E402
from app.services.rag.ingest import Ingestor  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]
KB_DIR = BACKEND.parent / "knowledge_base" / "documents"


@pytest.fixture(scope="session", autouse=True)
def migrated_db() -> None:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(cfg, "head")
    with SessionLocal() as db:
        Ingestor(db, HashEmbeddings(384)).ingest_dir(KB_DIR)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def llm() -> MockLLM:
    return MockLLM()


@pytest.fixture
def pipeline(db, llm) -> Pipeline:
    return Pipeline(db, llm, HashEmbeddings(384), get_settings())


@pytest.fixture
def client(llm):
    from app.main import app

    app.dependency_overrides[get_llm] = lambda: llm
    app.dependency_overrides[get_embeddings] = lambda: HashEmbeddings(384)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


DEMO = ("I received a WhatsApp message claiming to be from my bank. It asked me to click a link and "
        "enter my OTP because my account would otherwise be blocked.")
