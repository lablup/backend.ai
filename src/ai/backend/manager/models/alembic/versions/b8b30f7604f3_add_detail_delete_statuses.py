"""add_detail_delete_statuses

Revision ID: b8b30f7604f3
Revises: 360af8f33d4e
Create Date: 2022-10-24 13:35:41.852654

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "b8b30f7604f3"
down_revision = "360af8f33d4e"
branch_labels = None
depends_on = None

DELETING = "deleting"
enum_name = "vfolderoperationstatus"
ERROR = "error"
DELETE_ONGOING = "delete-ongoing"  # vfolder is moving to trash bin
DELETE_COMPLETE = "deleted-complete"  # vfolder is in trash bin
RECOVER_ONGOING = "recover-ongoing"  # vfolder is being recovered from trash bin
PURGE_ONGOING = "purge-ongoing"  # vfolder is being removed from trash bin
PURGE_COMPLETE = "purged-complete"  # vfolder is permanently removed


def upgrade():
    op.execute(f"ALTER TYPE {enum_name} RENAME VALUE '{DELETING}' TO '{DELETE_ONGOING}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{ERROR}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{DELETE_ONGOING}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{DELETE_COMPLETE}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{RECOVER_ONGOING}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{PURGE_ONGOING}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{PURGE_COMPLETE}'")
    op.add_column(
        "vfolders", sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null())
    )


def downgrade():
    op.execute(f"ALTER TYPE {enum_name} RENAME VALUE '{DELETE_ONGOING}' TO '{DELETING}'")
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{ERROR}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""
        )
    )
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{DELETE_ONGOING}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""
        )
    )
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{DELETE_COMPLETE}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""
        )
    )
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{RECOVER_ONGOING}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""
        )
    )
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{PURGE_ONGOING}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""
        )
    )
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{PURGE_COMPLETE}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""
        )
    )
    op.drop_column("vfolders", "status_history")
