"""add labels table

Revision ID: 96014c885c33
Revises: b7c1e93d40aa
Create Date: 2026-08-24 15:12:20.891336

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "96014c885c33"
down_revision = "b7c1e93d40aa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labels",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", GUID(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_labels")),
        sa.UniqueConstraint("entity_type", "entity_id", "key", "value", name="uq_labels_label"),
    )
    op.create_index("ix_labels_entity", "labels", ["entity_type", "entity_id"], unique=False)
    op.create_index("ix_labels_pair", "labels", ["key", "value"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_labels_pair", table_name="labels")
    op.drop_index("ix_labels_entity", table_name="labels")
    op.drop_table("labels")
