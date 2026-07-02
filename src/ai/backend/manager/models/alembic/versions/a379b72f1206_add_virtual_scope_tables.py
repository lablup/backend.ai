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
        "virtual_scope",
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_virtual_scope")),
        sa.UniqueConstraint("scope_type", "scope_id", name="uq_virtual_scope_scope"),
    )
    op.create_table(
        "association_virtual",
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
            ["virtual_scope.id"],
            name=op.f("fk_association_virtual_virtual_scope_id_virtual_scope"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_association_virtual")),
        sa.UniqueConstraint(
            "virtual_scope_id", "scope_type", "scope_id", name="uq_association_virtual_vs_scope"
        ),
    )
    op.create_index(
        "ix_association_virtual_scope",
        "association_virtual",
        ["scope_type", "scope_id"],
        unique=False,
    )
    op.create_table(
        "association_entity",
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
            ["virtual_scope.id"],
            name=op.f("fk_association_entity_virtual_scope_id_virtual_scope"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_association_entity")),
        sa.UniqueConstraint(
            "virtual_scope_id", "entity_type", "entity_id", name="uq_association_entity_vs_entity"
        ),
    )
    op.create_index(
        "ix_association_entity_entity",
        "association_entity",
        ["entity_type", "entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_association_entity_entity", table_name="association_entity")
    op.drop_table("association_entity")
    op.drop_index("ix_association_virtual_scope", table_name="association_virtual")
    op.drop_table("association_virtual")
    op.drop_table("virtual_scope")
