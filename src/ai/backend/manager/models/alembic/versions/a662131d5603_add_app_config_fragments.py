"""add app_config_fragments table

Adds the per-scope raw fragment table keyed by
`(scope_type, scope_id, name)`. `rank` (low → high) drives merge priority
within a `name`; it defaults to a per-scope_type tier on create and is
overridable. There is no separate policy table — `name` is a free-form
config key.

Revision ID: a662131d5603
Revises: c6648c039bd4
Create Date: 2026-04-24

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "a662131d5603"
down_revision = "c6648c039bd4"
# Part of: 26.6.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_config_fragments",
        IDColumn(),
        sa.Column(
            "scope_type",
            sa.String(length=32),
            nullable=False,
            index=True,
        ),
        sa.Column("scope_id", sa.String(length=255), nullable=False),
        sa.Column(
            "name",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "rank",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "config",
            pgsql.JSONB(),
            nullable=True,
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
            "scope_type",
            "scope_id",
            "name",
            name="uq_app_config_fragments_scope_name",
        ),
        sa.Index("ix_app_config_fragments_name_rank", "name", "rank"),
    )


def downgrade() -> None:
    op.drop_table("app_config_fragments")
