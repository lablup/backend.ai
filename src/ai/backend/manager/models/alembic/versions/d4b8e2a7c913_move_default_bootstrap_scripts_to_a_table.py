"""Move default bootstrap scripts to a table

`bootstrap_scripts.is_default` marked a user's default script. Each live marked script
becomes a `user_default_bootstrap_scripts` row, and the column goes.

Revision ID: d4b8e2a7c913
Revises: c5ea6e2fa389
Create Date: 2026-10-29 12:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "d4b8e2a7c913"
down_revision = "c5ea6e2fa389"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_default_bootstrap_scripts",
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("script_id", GUID(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_user_default_bootstrap_scripts")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name=op.f("fk_user_default_bootstrap_scripts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["script_id"],
            ["bootstrap_scripts.id"],
            name=op.f("fk_user_default_bootstrap_scripts_script_id_bootstrap_scripts"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_user_default_bootstrap_scripts_script_id"),
        "user_default_bootstrap_scripts",
        ["script_id"],
        unique=False,
    )
    op.execute(
        sa.text("""
            INSERT INTO user_default_bootstrap_scripts (user_id, script_id)
            SELECT b.entity_id, b.id
            FROM bootstrap_scripts AS b
            JOIN users AS u ON u.uuid = b.entity_id
            WHERE b.entity_type = 'user' AND b.is_default AND b.deleted_at IS NULL
            ON CONFLICT DO NOTHING
        """)
    )
    op.drop_index("uq_bootstrap_scripts_is_default", table_name="bootstrap_scripts")
    op.drop_column("bootstrap_scripts", "is_default")


def downgrade() -> None:
    op.add_column(
        "bootstrap_scripts",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        sa.text("""
            UPDATE bootstrap_scripts AS b
            SET is_default = true
            FROM user_default_bootstrap_scripts AS d
            WHERE b.id = d.script_id
        """)
    )
    op.create_index(
        "uq_bootstrap_scripts_is_default",
        "bootstrap_scripts",
        ["entity_type", "entity_id"],
        unique=True,
        postgresql_where=sa.text("is_default AND deleted_at IS NULL"),
    )
    op.drop_index(
        op.f("ix_user_default_bootstrap_scripts_script_id"),
        table_name="user_default_bootstrap_scripts",
    )
    op.drop_table("user_default_bootstrap_scripts")
