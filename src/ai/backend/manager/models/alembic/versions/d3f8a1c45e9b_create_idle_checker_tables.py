"""create idle_checker tables

Introduce the persistence foundation for the first-class idle checker
(BEP-1054). ``idle_checkers`` holds a reusable, scope-free checker spec
(``checker_type`` + JSONB ``spec``); ``idle_checker_bindings`` is the
scope <-> checker association carrying its own ``enabled`` flag. Scope is a
polymorphic ``(scope_type, scope_id)`` string pair validated on the write
path rather than by a DB foreign key.

Revision ID: d3f8a1c45e9b
Revises: a8e06485829f
Create Date: 2026-06-22

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "d3f8a1c45e9b"
down_revision = "a8e06485829f"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idle_checkers",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("checker_type", sa.String(length=64), nullable=False),
        sa.Column("spec", postgresql.JSONB(), nullable=False),
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
            nullable=False,
        ),
    )
    op.create_table(
        "idle_checker_bindings",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scope_type", sa.String(length=64), nullable=False),
        sa.Column("scope_id", GUID, nullable=False),
        sa.Column("idle_checker_id", GUID, nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
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
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["idle_checker_id"],
            ["idle_checkers.id"],
            name="fk_idle_checker_bindings_idle_checker_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "idle_checker_id",
            "scope_type",
            "scope_id",
            name="uq_idle_checker_bindings_checker_scope",
        ),
    )
    op.create_index(
        "ix_idle_checker_bindings_scope",
        "idle_checker_bindings",
        ["scope_type", "scope_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_idle_checker_bindings_scope", table_name="idle_checker_bindings")
    op.drop_table("idle_checker_bindings")
    op.drop_table("idle_checkers")
