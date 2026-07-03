"""add virtual scope tables

Revision ID: a379b72f1206
Revises: b4c5d6e7f8a9
Create Date: 2026-07-02 20:09:45.678449

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a379b72f1206"
down_revision = "b4c5d6e7f8a9"
# Part of: 26.7.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "virtual_scopes",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_virtual_scopes")),
        sa.UniqueConstraint("scope_type", "scope_id", name="uq_virtual_scopes_scope"),
    )
    op.create_table(
        "scope_bindings",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("virtual_scope_id", GUID(), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("permission_cap", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["virtual_scope_id"],
            ["virtual_scopes.id"],
            name=op.f("fk_scope_bindings_virtual_scope_id_virtual_scopes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scope_bindings")),
        sa.UniqueConstraint(
            "virtual_scope_id", "scope_type", "scope_id", name="uq_scope_bindings_vs_scope"
        ),
    )
    op.create_index(
        "ix_scope_bindings_scope",
        "scope_bindings",
        ["scope_type", "scope_id"],
        unique=False,
    )
    op.create_table(
        "entity_memberships",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("virtual_scope_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("permission_cap", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["virtual_scope_id"],
            ["virtual_scopes.id"],
            name=op.f("fk_entity_memberships_virtual_scope_id_virtual_scopes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entity_memberships")),
        sa.UniqueConstraint(
            "virtual_scope_id", "entity_type", "entity_id", name="uq_entity_memberships_vs_entity"
        ),
    )
    op.create_index(
        "ix_entity_memberships_entity",
        "entity_memberships",
        ["entity_type", "entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_entity_memberships_entity", table_name="entity_memberships")
    op.drop_table("entity_memberships")
    op.drop_index("ix_scope_bindings_scope", table_name="scope_bindings")
    op.drop_table("scope_bindings")
    op.drop_table("virtual_scopes")
