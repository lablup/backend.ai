"""Rename vfolderpermission PG enum type to vfoldermountpermission

Revision ID: ba4530_rename_vfolderpermission_type
Revises: ba4308_usage_entries
Create Date: 2026-02-18 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "ba4530_rename_vfolderpermission_type"
down_revision = "ba4308_usage_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the PostgreSQL enum type from vfolderpermission to vfoldermountpermission
    # to match the Python class name VFolderMountPermission (renamed from VFolderPermission in BA-2107).
    # EnumValueType auto-derives the PG type name from enum_cls.__name__.lower(),
    # so the DB type must match the Python class name.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vfolderpermission') THEN
                ALTER TYPE vfolderpermission RENAME TO vfoldermountpermission;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vfoldermountpermission') THEN
                ALTER TYPE vfoldermountpermission RENAME TO vfolderpermission;
            END IF;
        END$$;
        """
    )
