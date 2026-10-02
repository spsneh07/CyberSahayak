"""Ingest knowledge_base/documents into PostgreSQL/pgvector.

Usage (from backend/):  python -m scripts.ingest_kb [--dir PATH] [--no-prune]
"""
import argparse
from pathlib import Path

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.logging import setup_logging
from app.services.ai.factory import get_embeddings
from app.services.rag.ingest import Ingestor


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser()
    # documents/ (team-written summaries) + official/ (official texts fetched by scripts.fetch_official_kb)
    parser.add_argument("--dir", default=settings.knowledge_base_dir)
    parser.add_argument("--no-prune", action="store_true")
    args = parser.parse_args()
    setup_logging(settings.log_level)
    with SessionLocal() as db:
        report = Ingestor(db, get_embeddings()).ingest_dir(Path(args.dir), prune=not args.no_prune)
    print(f"embedding provider: {settings.embedding_provider} (dim {settings.embedding_dim})")
    print(report)


if __name__ == "__main__":
    main()
