"""create app_config_allow_list table

Introduce ``app_config_allow_list`` — the per-``(config_name, scope_type)``
write gate (BEP-1052). A config fragment at a given ``(config_name,
scope_type)`` may be written only if a row exists here; admins pre-configure
these. ``config_name`` is a foreign key into ``app_config_definitions`` so an
entry may only reference a registered config name.

Revision ID: 2d6443ac0d4a
Revises: 9fc9e6bfe695
Create Date: 2026-06-18

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "2d6443ac0d4a"
down_revision = "9fc9e6bfe695"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_config_allow_list",
        IDColumn(),
        sa.Column("config_name", sa.String(length=128), nullable=False),
        sa.Column("scope_type", sa.String(length=64), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["config_name"],
            ["app_config_definitions.config_name"],
            name="fk_app_config_allow_list_config_name",
            ondelete="NO ACTION",
        ),
        sa.UniqueConstraint(
            "config_name", "scope_type", name="uq_app_config_allow_list_config_name_scope_type"
        ),
    )


def downgrade() -> None:
    op.drop_table("app_config_allow_list")
