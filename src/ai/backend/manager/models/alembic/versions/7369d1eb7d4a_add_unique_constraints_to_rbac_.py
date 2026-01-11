"""add unique constraints to rbac permission tables

Revision ID: 7369d1eb7d4a
Revises: 84b901f69d16
Create Date: 2026-01-11 20:28:35.199474

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '7369d1eb7d4a'
down_revision = '84b901f69d16'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_object_permissions_role_entity_op",
        "object_permissions",
        ["role_id", "entity_type", "entity_id", "operation"],
    )
    op.create_unique_constraint(
        "uq_permission_groups_role_scope",
        "permission_groups",
        ["role_id", "scope_type", "scope_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_permission_groups_role_scope",
        "permission_groups",
        type_="unique",
    )
    op.drop_constraint(
        "uq_object_permissions_role_entity_op",
        "object_permissions",
        type_="unique",
    )
