"""drop legacy app_configs table

Removes the predecessor `app_configs` table and its enum type as
preparation for BEP-1052 (Scoped App Config Redesign). The
replacement tables (`app_config_fragments`, `app_config_policies`)
are introduced in a follow-up migration on top of this one — the
new shape is incompatible with the old (different scope enum,
different unique key) so no in-place data migration is attempted.

Revision ID: 84d5c6daf8cc
Revises: f3a8c1d05e64
Create Date: 2026-04-24

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "84d5c6daf8cc"
down_revision = "f3a8c1d05e64"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("app_configs")
    op.execute("DROP TYPE IF EXISTS app_config_scope_type")


def downgrade() -> None:
    # Recreate the predecessor table to allow `alembic downgrade` to
    # complete cleanly. Existing-row restoration is not attempted.
    app_config_scope_type = sa.Enum("DOMAIN", "PROJECT", "USER", name="app_config_scope_type")
    op.create_table(
        "app_configs",
        IDColumn(),
        sa.Column(
            "scope_type",
            app_config_scope_type,
            nullable=False,
            index=True,
        ),
        sa.Column("scope_id", sa.String(length=256), nullable=False, index=True),
        sa.Column(
            "extra_config",
            pgsql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.UniqueConstraint("scope_type", "scope_id", name="uq_app_configs_scope"),
    )
