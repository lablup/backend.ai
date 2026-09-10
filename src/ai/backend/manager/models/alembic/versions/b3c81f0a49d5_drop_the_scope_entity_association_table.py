"""Drop the scope-entity association table

``association_scopes_entities`` has no reader left: the scope-entity relation is
answered by the own edges of the virtual entity graph, which is rebuilt from the
source tables. Nothing in the association table is unique to it, so the rows are
dropped rather than moved.

The downgrade recreates the table empty.

Create Date: 2026-09-10

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "b3c81f0a49d5"
down_revision = "c092d242a027"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("association_scopes_entities")


def downgrade() -> None:
    op.create_table(
        "association_scopes_entities",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("relation_type", sa.String(length=32), server_default="auto", nullable=False),
        sa.Column("permission_cap", sa.Integer(), nullable=True),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_association_scopes_entities")),
        sa.UniqueConstraint("scope_type", "scope_id", "entity_id", name="uq_scope_id_entity_id"),
    )
    op.create_index(
        "ix_association_scopes_entities_entity",
        "association_scopes_entities",
        ["entity_type", "entity_id"],
    )
