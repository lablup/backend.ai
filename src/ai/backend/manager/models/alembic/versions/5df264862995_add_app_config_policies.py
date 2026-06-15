"""add app_config_policies table

Adds the per-document policy table — `config_name` (UNIQUE) and
`scope_sources` (ordered scope chain). These are intended to drive the
merge order and write allow-list; the enforcing logic lands in a
follow-up PR (this migration only creates the table).

A sister migration (BA-5827) will stack on top with the
`app_config_fragments` table, which is planned to FK to `config_name`.

Revision ID: 5df264862995
Revises: c6648c039bd4
Create Date: 2026-04-24

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "5df264862995"
down_revision = "c6648c039bd4"
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
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "config_name",
            name="uq_app_config_policies_config_name",
        ),
    )


def downgrade() -> None:
    op.drop_table("app_config_policies")
