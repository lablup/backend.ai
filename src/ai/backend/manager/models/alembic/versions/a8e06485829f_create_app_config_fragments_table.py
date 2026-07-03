"""create app_config_fragments table

Introduce ``app_config_fragments`` — the single source-of-truth table for
scoped app-config values (BEP-1052). Each row is one JSON ``config`` document
at a ``(config_name, scope_type, scope_id)`` natural key, carrying a ``rank``
that orders fragments for the deep-merge that produces the merged ``AppConfig``
view. ``config_name`` references the registered set in
``app_config_definitions``.

Revision ID: a8e06485829f
Revises: 2d6443ac0d4a
Create Date: 2026-06-18

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "a8e06485829f"
down_revision = "2d6443ac0d4a"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_config_fragments",
        IDColumn(),
        sa.Column(
            "config_name",
            sa.String(length=128),
            sa.ForeignKey("app_config_definitions.config_name", ondelete="NO ACTION"),
            nullable=False,
        ),
        sa.Column("scope_type", sa.String(length=64), nullable=False),
        sa.Column("scope_id", sa.String(length=255), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("config", JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "config_name",
            "scope_type",
            "scope_id",
            name="uq_app_config_fragments_config_name_scope_type_scope_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("app_config_fragments")
