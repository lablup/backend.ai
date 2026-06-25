"""create app_config_allow_list table

Introduce ``app_config_allow_list`` (BEP-1052). Each row grants permission to
write config fragments for one ``(config_name, scope_type)``: a config fragment
at that ``(config_name, scope_type)`` may be created, updated, or purged only if
a row exists here, and admins pre-configure these rows. ``config_name`` is a
foreign key into ``app_config_definitions`` so an entry may only reference a
registered config name.

Revision ID: 2d6443ac0d4a
Revises: c7e1a9d4f6b2
Create Date: 2026-06-18

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "2d6443ac0d4a"
down_revision = "c7e1a9d4f6b2"
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
