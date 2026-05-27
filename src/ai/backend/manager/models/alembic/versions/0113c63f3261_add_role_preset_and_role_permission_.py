"""add role_preset and role_permission_preset tables

Adds two new tables that support admin-managed role templates:

- ``role_presets`` — one row per template, identified by ``scope_type``
  with an optional ``auto_apply`` flag. A partial unique index ensures
  at most one auto-apply preset per scope type.
- ``role_permission_presets`` — child rows that capture the
  ``(entity_type, operation)`` pairs that the preset grants. Deleting
  a preset cascades to its permission rows.

Create Date: 2026-05-27

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "0113c63f3261"
down_revision = "338bc3284f20"
# Part of: 26.6.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role_presets",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column(
            "auto_apply",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_presets")),
    )
    op.create_index(
        "uq_role_presets_scope_type_auto_apply",
        "role_presets",
        ["scope_type"],
        unique=True,
        postgresql_where=sa.text("auto_apply IS TRUE"),
    )
    op.create_table(
        "role_permission_presets",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("role_preset_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_preset_id"],
            ["role_presets.id"],
            name=op.f("fk_role_permission_presets_role_preset_id_role_presets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_permission_presets")),
        sa.UniqueConstraint(
            "role_preset_id",
            "entity_type",
            "operation",
            name="uq_role_permission_presets_preset_entity_op",
        ),
    )


def downgrade() -> None:
    op.drop_table("role_permission_presets")
    op.drop_index(
        "uq_role_presets_scope_type_auto_apply",
        table_name="role_presets",
        postgresql_where=sa.text("auto_apply IS TRUE"),
    )
    op.drop_table("role_presets")
