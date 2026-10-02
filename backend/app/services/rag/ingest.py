"""Knowledge ingestion: parse -> clean -> sanitise -> chunk -> embed -> store (pgvector)."""
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.repositories.knowledge import KnowledgeRepository
from app.services.ai.base import EmbeddingProvider
from app.services.rag.chunker import chunk_text
from app.services.rag.sanitize import clean_text, strip_injections

log = logging.getLogger(__name__)

REQUIRED_META = ("title", "organization", "url", "category", "document_type", "source_note")
SUPPORTED = {".md", ".txt", ".pdf"}


@dataclass
class IngestReport:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    chunks: int = 0
    skipped: list[str] | None = None
    injection_lines_removed: int = 0


def parse_front_matter(raw: str) -> tuple[dict[str, str | None], str]:
    if not raw.startswith("---"):
        return {}, raw
    _, header, body = raw.split("---", 2)
    meta: dict[str, str | None] = {}
    for line in header.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip() or None
    return meta, body


def load_document(path: Path) -> tuple[dict[str, str | None], str]:
    if path.suffix == ".pdf":
        from pypdf import PdfReader

        meta_path = path.with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        text = "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        return meta, text
    return parse_front_matter(path.read_text(encoding="utf-8"))


class Ingestor:
    def __init__(self, db: Session, embeddings: EmbeddingProvider) -> None:
        self.repo = KnowledgeRepository(db)
        self.embeddings = embeddings

    def ingest_dir(self, directory: Path, prune: bool = True) -> IngestReport:
        report = IngestReport(skipped=[])
        seen: set[str] = set()
        for path in sorted(directory.rglob("*")):
            if path.suffix.lower() not in SUPPORTED or path.name.lower() == "readme.md":
                continue
            rel = path.relative_to(directory).as_posix()
            seen.add(rel)
            try:
                status, n, removed = self.ingest_file(path, rel)
            except ValueError as exc:
                report.skipped.append(f"{rel}: {exc}")
                continue
            report.injection_lines_removed += removed
            setattr(report, status, getattr(report, status) + 1)
            report.chunks += n
        if prune:
            report.removed = self.repo.delete_missing(seen)
        return report

    def ingest_file(self, path: Path, rel: str) -> tuple[str, int, int]:
        meta, raw = load_document(path)
        missing = [k for k in REQUIRED_META if not meta.get(k)]
        if missing:
            raise ValueError(f"missing metadata {missing}")
        if not str(meta["url"]).lower().startswith(("https://", "http://")):
            raise ValueError("url must be an http(s) URL")
        text, removed = strip_injections(clean_text(raw))
        if removed:
            log.warning("removed %d instruction-like lines from %s", removed, rel)
        # Embedding identity is part of the hash so switching provider/model re-embeds everything.
        digest = hashlib.sha256(
            (self.embeddings.identity + json.dumps(meta, sort_keys=True) + text).encode()
        ).hexdigest()
        existing = self.repo.get_by_path(rel)
        if existing and existing.content_hash == digest:
            return "unchanged", 0, removed
        chunks = chunk_text(text, title=str(meta["title"]))
        if not chunks:
            raise ValueError("no text content")
        vectors = self.embeddings.embed(chunks)
        self.repo.upsert_document(meta, rel, digest, list(zip(chunks, vectors)), self.embeddings.identity)
        return ("updated" if existing else "added"), len(chunks), removed
