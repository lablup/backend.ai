"""add app_config_policies table

Adds the per-document policy table — `config_name` (UNIQUE, immutable)
and `scope_sources` (ordered scope chain) drive the merge order and
the write allow-list.

Sister migration BA-5827 stacks on top with the
`app_config_fragments` table (which FKs to `config_name`).

Revision ID: 5df264862995
Revises: 5d08e1164834
Create Date: 2026-04-24

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "5df264862995"
down_revision = "5d08e1164834"
# Part of: 26.6.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_config_policies",
        IDColumn(),
        sa.Column("config_name", sa.String(length=128), nullable=False),
        sa.Column(
            "scope_sources",
            sa.ARRAY(sa.String(length=64)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "config_name",
            name="uq_app_config_policies_config_name",
        ),
    )


def downgrade() -> None:
    op.drop_table("app_config_policies")
