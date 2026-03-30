"""add entity_fields table

Revision ID: d86417a6bf7b
Revises: d0a3c0716970
Create Date: 2026-01-05 19:25:49.581618

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "d86417a6bf7b"
down_revision = "d0a3c0716970"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_fields",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("field_type", sa.String(length=64), nullable=False),
        sa.Column("field_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entity_fields")),
        sa.UniqueConstraint(
            "entity_type",
            "entity_id",
            "field_type",
            "field_id",
            name="uq_entity_fields_mapping",
        ),
    )
    op.create_index(
        "ix_entity_fields_entity_lookup",
        "entity_fields",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_entity_fields_field_lookup",
        "entity_fields",
        ["field_type", "field_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_entity_fields_field_lookup", table_name="entity_fields")
    op.drop_index("ix_entity_fields_entity_lookup", table_name="entity_fields")
    op.drop_table("entity_fields")
