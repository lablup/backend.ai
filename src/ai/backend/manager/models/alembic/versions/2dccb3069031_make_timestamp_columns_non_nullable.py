"""make timestamp columns non-nullable

Lifecycle timestamps (``created_at`` / ``modified_at`` / ``updated_at``) are
semantically always present but were declared nullable across legacy tables.
Renames the legacy ``modified_at`` columns of users / keypairs / groups /
vfolder_invitations to ``updated_at``, backfills NULLs, and sets NOT NULL.
Columns that lacked an insert-time default additionally gain a ``now()``
server default.

Revision ID: 2dccb3069031
Revises: e3f2ff64863f
Create Date: 2026-08-06 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2dccb3069031"
down_revision = "e3f2ff64863f"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_RENAMED_TABLES = ("users", "keypairs", "groups", "vfolder_invitations")

# (table, column, backfill expression) — pairs backfill created_at from the
# sibling timestamp first, so the sibling's own backfill sees a non-NULL value.
_TARGETS = (
    ("users", "created_at", "COALESCE(updated_at, now())"),
    ("users", "updated_at", "COALESCE(created_at, now())"),
    ("users", "password_changed_at", "COALESCE(created_at, now())"),
    ("keypairs", "created_at", "COALESCE(updated_at, now())"),
    ("keypairs", "updated_at", "COALESCE(created_at, now())"),
    ("groups", "created_at", "COALESCE(updated_at, now())"),
    ("groups", "updated_at", "COALESCE(created_at, now())"),
    ("networks", "created_at", "COALESCE(updated_at, now())"),
    ("networks", "updated_at", "COALESCE(created_at, now())"),
    ("vfolders", "created_at", "COALESCE(updated_at, now())"),
    ("vfolder_invitations", "created_at", "COALESCE(updated_at, now())"),
    ("vfolder_invitations", "updated_at", "COALESCE(created_at, now())"),
    ("model_cards", "updated_at", "COALESCE(created_at, now())"),
    ("role_invitations", "updated_at", "COALESCE(created_at, now())"),
    ("runtime_variants", "updated_at", "COALESCE(created_at, now())"),
    ("runtime_variant_presets", "updated_at", "COALESCE(created_at, now())"),
    ("deployment_revision_presets", "updated_at", "COALESCE(created_at, now())"),
    ("deployment_auto_scaling_policies", "updated_at", "COALESCE(created_at, now())"),
    ("error_logs", "created_at", "now()"),
    ("images", "created_at", "now()"),
    ("keypair_resource_policies", "created_at", "now()"),
    ("user_resource_policies", "created_at", "now()"),
    ("project_resource_policies", "created_at", "now()"),
    ("scaling_groups", "created_at", "now()"),
    ("session_templates", "created_at", "now()"),
    ("sessions", "created_at", "now()"),
    ("kernels", "created_at", "now()"),
)

# Columns that had no insert-time default at all.
_GAIN_SERVER_DEFAULT = (
    ("vfolder_invitations", "updated_at"),
    ("model_cards", "updated_at"),
    ("role_invitations", "updated_at"),
    ("runtime_variants", "updated_at"),
    ("runtime_variant_presets", "updated_at"),
    ("deployment_revision_presets", "updated_at"),
    ("deployment_auto_scaling_policies", "updated_at"),
)


def upgrade() -> None:
    for table in _RENAMED_TABLES:
        op.alter_column(table, "modified_at", new_column_name="updated_at")
    for table, column, backfill in _TARGETS:
        op.execute(sa.text(f"UPDATE {table} SET {column} = {backfill} WHERE {column} IS NULL"))
        op.alter_column(table, column, nullable=False)
    for table, column in _GAIN_SERVER_DEFAULT:
        op.alter_column(table, column, server_default=sa.text("now()"))


def downgrade() -> None:
    for table, column in reversed(_GAIN_SERVER_DEFAULT):
        op.alter_column(table, column, server_default=None)
    for table, column, _ in reversed(_TARGETS):
        op.alter_column(table, column, nullable=True)
    for table in reversed(_RENAMED_TABLES):
        op.alter_column(table, "updated_at", new_column_name="modified_at")
