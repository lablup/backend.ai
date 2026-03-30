"""add role tables

Revision ID: 60bcbf00a96e
Revises: bf39b34717d4
Create Date: 2025-07-08 17:07:24.636221

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "60bcbf00a96e"
down_revision = "bf39b34717d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resource_permissions",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resource_permissions")),
    )
    op.create_table(
        "role_permissions",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_permissions")),
    )
    op.create_table(
        "roles",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("state", sa.VARCHAR(length=16), server_default="active", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("state", sa.VARCHAR(length=16), server_default="active", nullable=False),
        sa.Column("granted_by", GUID(), nullable=True),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_roles")),
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("role_permissions")
    op.drop_table("resource_permissions")
