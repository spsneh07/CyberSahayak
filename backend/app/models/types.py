"""Portable column types: pgvector on PostgreSQL, JSON elsewhere (tests)."""
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class EmbeddingVector(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int) -> None:
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return [float(v) for v in value]

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return [float(v) for v in value]
