"""add fk constraints to rbac tables

Revision ID: 3727dd0927cf
Revises: 19e48e70b86a
Create Date: 2026-03-24 00:00:00.000000

"""

import textwrap

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3727dd0927cf"
down_revision = "19e48e70b86a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1: Clean up orphan rows in permissions where role_id has no matching roles.id
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM permissions p
                WHERE NOT EXISTS (
                    SELECT 1 FROM roles r WHERE r.id = p.role_id
                )
            """)
        )
    )

    # Step 2: Clean up orphan rows in user_roles where user_id has no matching users.uuid
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM user_roles ur
                WHERE NOT EXISTS (
                    SELECT 1 FROM users u WHERE u.uuid = ur.user_id
                )
            """)
        )
    )

    # Step 3: Clean up orphan rows in user_roles where role_id has no matching roles.id
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM user_roles ur
                WHERE NOT EXISTS (
                    SELECT 1 FROM roles r WHERE r.id = ur.role_id
                )
            """)
        )
    )

    # Step 4: Add FK constraint permissions.role_id -> roles.id
    op.create_foreign_key(
        op.f("fk_permissions_role_id_roles"),
        "permissions",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Step 5: Add FK constraint user_roles.user_id -> users.uuid
    op.create_foreign_key(
        op.f("fk_user_roles_user_id_users"),
        "user_roles",
        "users",
        ["user_id"],
        ["uuid"],
        ondelete="CASCADE",
    )

    # Step 6: Add FK constraint user_roles.role_id -> roles.id
    op.create_foreign_key(
        op.f("fk_user_roles_role_id_roles"),
        "user_roles",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_user_roles_role_id_roles"),
        "user_roles",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_user_roles_user_id_users"),
        "user_roles",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_permissions_role_id_roles"),
        "permissions",
        type_="foreignkey",
    )
