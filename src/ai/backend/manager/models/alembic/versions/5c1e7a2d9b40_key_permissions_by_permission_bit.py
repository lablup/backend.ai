"""key permissions by the permission bit and drop operation

Revision ID: 5c1e7a2d9b40
Revises: d4e6f8a0b2c3
Create Date: 2026-09-03

"""

import sqlalchemy as sa
from alembic import op

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "5c1e7a2d9b40"
down_revision = "d4e6f8a0b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # grant:* rows carry no bit; sharing is judged from entity shares and scope CREATE.
    op.execute(sa.text("DELETE FROM permissions WHERE permission = 0"))
    op.drop_constraint("uq_permissions_role_scope_entity_op", "permissions", type_="unique")
    op.drop_column("permissions", "operation")
    op.create_unique_constraint(
        "uq_permissions_role_scope_entity_permission",
        "permissions",
        ["role_id", "scope_type", "scope_id", "entity_type", "permission"],
    )
    op.create_check_constraint(
        op.f("ck_permissions_single_bit"),
        "permissions",
        "permission > 0 AND (permission & (permission - 1)) = 0",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_permissions_single_bit"), "permissions", type_="check")
    op.drop_constraint("uq_permissions_role_scope_entity_permission", "permissions", type_="unique")
    op.add_column(
        "permissions",
        sa.Column("operation", sa.String(length=32), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE permissions SET operation = CASE permission"
            " WHEN 1 THEN 'read' WHEN 2 THEN 'update' WHEN 4 THEN 'create'"
            " WHEN 8 THEN 'soft-delete' WHEN 16 THEN 'hard-delete' END"
        )
    )
    op.alter_column("permissions", "operation", nullable=False)
    op.create_unique_constraint(
        "uq_permissions_role_scope_entity_op",
        "permissions",
        ["role_id", "scope_type", "scope_id", "entity_type", "operation"],
    )
