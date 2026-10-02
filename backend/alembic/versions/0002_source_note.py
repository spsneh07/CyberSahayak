"""knowledge_documents: source_note (provenance) and embedding_identity (model used for its vectors)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-02
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_documents", sa.Column("source_note", sa.Text(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("embedding_identity", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("knowledge_documents", "embedding_identity")
    op.drop_column("knowledge_documents", "source_note")
