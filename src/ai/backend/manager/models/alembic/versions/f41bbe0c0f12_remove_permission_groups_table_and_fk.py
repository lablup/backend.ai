"""remove_permission_groups_table_and_fk

Revision ID: f41bbe0c0f12
Revises: 8fd6f47bd226
Create Date: 2026-02-11 02:43:17.099347

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "f41bbe0c0f12"
down_revision = "8fd6f47bd226"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop FK constraints from permissions and object_permissions
    op.drop_constraint(
        op.f("fk_permissions_permission_group_id_permission_groups"),
        "permissions",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_object_permissions_permission_group_id_permission_groups"),
        "object_permissions",
        type_="foreignkey",
    )

    # Drop indexes on permission_group_id columns
    op.drop_index("ix_id_permission_group_id", table_name="permissions")
    op.drop_index("ix_object_permissions_permission_group_id", table_name="object_permissions")

    # Drop permission_group_id columns
    op.drop_column("permissions", "permission_group_id")
    op.drop_column("object_permissions", "permission_group_id")

    # Drop indexes and constraints on permission_groups table
    op.drop_index("ix_id_role_id_scope_id", table_name="permission_groups")
    op.drop_constraint("uq_permission_groups_role_scope", "permission_groups", type_="unique")

    # Drop permission_groups table
    op.drop_table("permission_groups")


def downgrade() -> None:
    conn = op.get_bind()

    # Recreate permission_groups table
    op.create_table(
        "permission_groups",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("scope_type", sa.VARCHAR(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permission_groups")),
    )
    op.create_index(
        "ix_id_role_id_scope_id", "permission_groups", ["id", "role_id", "scope_id"], unique=False
    )
    op.create_unique_constraint(
        "uq_permission_groups_role_scope",
        "permission_groups",
        ["role_id", "scope_type", "scope_id"],
    )

    # Add permission_group_id columns as nullable first (backfill needed)
    op.add_column(
        "permissions",
        sa.Column("permission_group_id", GUID(), nullable=True),
    )
    op.add_column(
        "object_permissions",
        sa.Column("permission_group_id", GUID(), nullable=True),
    )

    # Backfill: create a GLOBAL-scope permission_group per role_id found in
    # object_permissions, then point every row at it.
    permissions_t = sa.table(
        "permissions",
        sa.column("id", GUID()),
        sa.column("permission_group_id", GUID()),
    )
    object_permissions_t = sa.table(
        "object_permissions",
        sa.column("id", GUID()),
        sa.column("role_id", GUID()),
        sa.column("permission_group_id", GUID()),
    )
    permission_groups_t = sa.table(
        "permission_groups",
        sa.column("id", GUID()),
        sa.column("role_id", GUID()),
        sa.column("scope_type", sa.VARCHAR(length=32)),
        sa.column("scope_id", sa.String(length=64)),
    )

    # Collect distinct role_ids from object_permissions
    role_ids = {
        row[0]
        for row in conn.execute(sa.select(object_permissions_t.c.role_id).distinct()).fetchall()
    }

    for role_id in role_ids:
        # Create a GLOBAL permission_group for each role
        pg_id = conn.execute(
            sa.insert(permission_groups_t)
            .values(role_id=role_id, scope_type="GLOBAL", scope_id="*")
            .returning(permission_groups_t.c.id)
        ).scalar_one()

        # Backfill object_permissions
        conn.execute(
            sa.update(object_permissions_t)
            .where(object_permissions_t.c.role_id == role_id)
            .values(permission_group_id=pg_id)
        )

    # Backfill permissions (no role_id column) — assign to first available
    # permission_group if any exist.
    first_pg = conn.execute(sa.select(permission_groups_t.c.id).limit(1)).scalar()
    if first_pg is not None:
        conn.execute(
            sa.update(permissions_t)
            .where(permissions_t.c.permission_group_id.is_(None))
            .values(permission_group_id=first_pg)
        )

    # Set columns to NOT NULL
    op.alter_column("permissions", "permission_group_id", nullable=False)
    op.alter_column("object_permissions", "permission_group_id", nullable=False)

    # Restore indexes
    op.create_index(
        "ix_id_permission_group_id", "permissions", ["id", "permission_group_id"], unique=False
    )
    op.create_index(
        "ix_object_permissions_permission_group_id",
        "object_permissions",
        ["permission_group_id"],
        unique=False,
    )

    # Restore FK constraints
    op.create_foreign_key(
        op.f("fk_permissions_permission_group_id_permission_groups"),
        "permissions",
        "permission_groups",
        ["permission_group_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_object_permissions_permission_group_id_permission_groups"),
        "object_permissions",
        "permission_groups",
        ["permission_group_id"],
        ["id"],
        ondelete="CASCADE",
    )
