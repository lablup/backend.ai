"""change permission table names

Revision ID: 643deb439458
Revises: ed84197be4fe
Create Date: 2025-07-11 22:10:52.126619

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "643deb439458"
down_revision = "ed84197be4fe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("role_permissions", "scope_permissions")
    op.drop_constraint("pk_role_permissions", "scope_permissions", type_="primary")
    op.create_primary_key("pk_scope_permissions", "scope_permissions", ["id"])

    op.rename_table("resource_permissions", "object_permissions")
    op.drop_constraint("pk_resource_permissions", "object_permissions", type_="primary")
    op.create_primary_key("pk_object_permissions", "object_permissions", ["id"])

    op.drop_column("user_roles", "state")
    op.add_column(
        "scope_permissions",
        sa.Column(
            "state",
            sa.VARCHAR(length=16),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "object_permissions",
        sa.Column(
            "state",
            sa.VARCHAR(length=16),
            nullable=False,
            server_default="active",
        ),
    )


def downgrade() -> None:
    op.rename_table("scope_permissions", "role_permissions")
    op.drop_constraint("pk_scope_permissions", "role_permissions", type_="primary")
    op.create_primary_key("pk_role_permissions", "role_permissions", ["id"])

    op.rename_table("object_permissions", "resource_permissions")
    op.drop_constraint("pk_object_permissions", "resource_permissions", type_="primary")
    op.create_primary_key("pk_resource_permissions", "resource_permissions", ["id"])

    op.add_column(
        "user_roles",
        sa.Column(
            "state",
            sa.VARCHAR(length=16),
            nullable=False,
            server_default="active",
        ),
    )
    op.drop_column("role_permissions", "state")
    op.drop_column("resource_permissions", "state")
