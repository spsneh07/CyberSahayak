"""initial schema with pgvector

Revision ID: 0001
Revises:
Create Date: 2026-10-02
"""
import sqlalchemy as sa
from alembic import op

from app.core.config import get_settings
from app.models.types import EmbeddingVector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    is_pg = op.get_bind().dialect.name == "postgresql"
    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("display_name", sa.String(120)),
        sa.Column("created_at", TS),
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("created_at", TS),
        sa.Column("updated_at", TS),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("intent", sa.String(40)),
        sa.Column("payload", sa.JSON),
        sa.Column("created_at", TS),
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), index=True),
        sa.Column("incident_type", sa.String(60)),
        sa.Column("subtype", sa.String(120)),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("platform", sa.String(120)),
        sa.Column("financial_loss", sa.Boolean),
        sa.Column("amount", sa.Float),
        sa.Column("currency", sa.String(8)),
        sa.Column("date_time", sa.String(80)),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("created_at", TS),
        sa.Column("updated_at", TS),
    )
    op.create_table(
        "classifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("subtype", sa.String(120)),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("alternatives", sa.JSON, nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("created_at", TS),
    )
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("item", sa.Text, nullable=False),
        sa.Column("why", sa.Text, nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("already_available", sa.Boolean, nullable=False),
        sa.Column("created_at", TS),
    )
    op.create_table(
        "complaint_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subject", sa.String(300), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("placeholders", sa.JSON, nullable=False),
        sa.Column("created_at", TS),
    )
    op.create_table(
        "awareness_content",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id", ondelete="CASCADE"), index=True),
        sa.Column("content", sa.JSON, nullable=False),
        sa.Column("created_at", TS),
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("organization", sa.String(200), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("category", sa.String(60), nullable=False, index=True),
        sa.Column("published_date", sa.String(40)),
        sa.Column("document_type", sa.String(60), nullable=False),
        sa.Column("source_path", sa.String(500), nullable=False, unique=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", TS),
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", EmbeddingVector(get_settings().embedding_dim), nullable=False),
    )
    if is_pg:
        op.execute(
            "CREATE INDEX ix_knowledge_chunks_embedding ON knowledge_chunks "
            "USING hnsw (embedding vector_cosine_ops)"
        )
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("message_id", sa.String(36), sa.ForeignKey("messages.id", ondelete="CASCADE")),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", TS),
    )


def downgrade() -> None:
    for table in [
        "feedback", "knowledge_chunks", "knowledge_documents", "awareness_content",
        "complaint_drafts", "evidence_items", "classifications", "incidents",
        "messages", "conversations", "users",
    ]:
        op.drop_table(table)
