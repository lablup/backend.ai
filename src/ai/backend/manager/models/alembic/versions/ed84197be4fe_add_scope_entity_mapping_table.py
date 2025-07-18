"""add scope entity mapping table

Revision ID: ed84197be4fe
Revises: a5ef73b01e97
Create Date: 2025-07-11 22:16:00.414113

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ed84197be4fe"
down_revision = "a5ef73b01e97"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "association_scopes_entities",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_association_scopes_entities")),
        sa.UniqueConstraint("scope_id", "entity_id", name="uq_scope_id_entity_id"),
    )


def downgrade() -> None:
    op.drop_table("association_scopes_entities")
