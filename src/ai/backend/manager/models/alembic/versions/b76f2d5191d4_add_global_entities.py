"""Add global entities

Add the `global` and `public` singleton scopes: their rows and their graph nodes with the
self edges every node carries.

Revision ID: b76f2d5191d4
Revises: a0f597deb5e5
Create Date: 2026-09-18

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.global_entity.seed import SEED_GLOBAL_ENTITIES_SQL

# revision identifiers, used by Alembic.
revision = "b76f2d5191d4"  # Part of: NEXT_RELEASE_VERSION
down_revision = "a0f597deb5e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "global_entities",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("name", sa.String(length=32), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    conn = op.get_bind()
    for statement in SEED_GLOBAL_ENTITIES_SQL:
        conn.execute(sa.text(statement))


def downgrade() -> None:
    conn = op.get_bind()
    # The edges go with the nodes by cascade.
    conn.execute(sa.text("DELETE FROM virtual_entities WHERE entity_type = 'global'"))
    op.drop_table("global_entities")
