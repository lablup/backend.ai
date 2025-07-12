"""change permission table names

Revision ID: 643deb439458
Revises: 60bcbf00a96e
Create Date: 2025-07-11 22:10:52.126619

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "643deb439458"
down_revision = "60bcbf00a96e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("role_permissions", "scope_permissions")
    op.drop_constraint("pk_role_permissions", "scope_permissions", type_="primary")
    op.create_primary_key("pk_scope_permissions", "scope_permissions", ["id"])

    op.rename_table("resource_permissions", "object_permissions")
    op.drop_constraint("pk_resource_permissions", "object_permissions", type_="primary")
    op.create_primary_key("pk_object_permissions", "object_permissions", ["id"])


def downgrade() -> None:
    op.rename_table("scope_permissions", "role_permissions")
    op.drop_constraint("pk_scope_permissions", "role_permissions", type_="primary")
    op.create_primary_key("pk_role_permissions", "role_permissions", ["id"])

    op.rename_table("object_permissions", "resource_permissions")
    op.drop_constraint("pk_object_permissions", "resource_permissions", type_="primary")
    op.create_primary_key("pk_resource_permissions", "resource_permissions", ["id"])
