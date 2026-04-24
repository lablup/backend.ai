"""add app_config_fragments and app_config_policies tables

Lands the data-layer foundation for BEP-1052 (Scoped App Config
Redesign):

- `app_config_policies`: per-document policy table — config_name
  (UNIQUE, immutable) and scope_sources (ordered scope chain).
  Drives the merge order and write allow-list.
- `app_config_fragments`: per-scope raw rows keyed by
  `(scope_type, scope_id, name)`. `name` is a FK to
  `app_config_policies.config_name` with default NO ACTION (the
  required-policy invariant — see BEP-1052 §1).

User-path writes are intentionally not supported yet, so policies
do not carry a `user_writable` flag.

Revision ID: 5df264862995
Revises: 84d5c6daf8cc
Create Date: 2026-04-24

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "5df264862995"
down_revision = "84d5c6daf8cc"
# Part of: 26.5.0
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
            sa.ForeignKey(
                # No ON DELETE / ON UPDATE — Postgres default NO ACTION
                # enforces the required-policy invariant: a policy
                # cannot be dropped while fragments reference it, and
                # config_name is immutable so ON UPDATE never fires.
                "app_config_policies.config_name",
                name="fk_app_config_fragments_name_app_config_policies_config_name",
            ),
            nullable=False,
        ),
        sa.Column(
            "extra_config",
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
            nullable=True,
        ),
        sa.UniqueConstraint(
            "scope_type",
            "scope_id",
            "name",
            name="uq_app_config_fragments_scope_name",
        ),
    )


def downgrade() -> None:
    op.drop_table("app_config_fragments")
    op.drop_table("app_config_policies")
