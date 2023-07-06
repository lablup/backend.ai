"""add_vfolder_purge_status

Revision ID: 3a3fbd3963fd
Revises: 69c059996cbd
Create Date: 2023-07-06 16:17:31.394295

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import text

from ai.backend.manager.models.base import GUID, convention

# revision identifiers, used by Alembic.
revision = "3a3fbd3963fd"
down_revision = "69c059996cbd"
branch_labels = None
depends_on = None


DELETING = "deleting"
enum_name = "vfolderoperationstatus"
ERROR = "error"
DELETE_ONGOING = "delete-ongoing"  # vfolder is moving to trash bin
DELETE_COMPLETE = "deleted-complete"  # vfolder is in trash bin
# RECOVER_ONGOING = "recover-ongoing"  # vfolder is being recovered from trash bin
PURGE_ONGOING = "purge-ongoing"  # vfolder is being removed from trash bin


def upgrade():
    op.execute(f"ALTER TYPE {enum_name} RENAME VALUE '{DELETING}' TO '{DELETE_ONGOING}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{ERROR}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{DELETE_COMPLETE}'")
    # op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{RECOVER_ONGOING}'")
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{PURGE_ONGOING}'")
    op.add_column(
        "vfolders", sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null())
    )


def downgrade():
    connection = op.get_bind()
    metadata = sa.MetaData(naming_convention=convention)
    vfolders = sa.Table(
        "vfolders",
        metadata,
        sa.Column(
            "id",
            GUID(),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "status",
            ENUM,
            nullable=False,
        ),
    )
    vfolder_delete_query = sa.delete(vfolders).where(
        vfolders.c.status.in_([DELETE_COMPLETE, PURGE_ONGOING])
    )
    connection.execute(vfolder_delete_query)

    vfolder_update_query = (
        sa.update(vfolders).where(vfolders.c.status == ERROR).values({"status": "ready"})
    )
    connection.execute(vfolder_update_query)

    op.execute(f"ALTER TYPE {enum_name} RENAME VALUE '{DELETE_ONGOING}' TO '{DELETING}'")

    op.execute(text(f"""DELETE FROM pg_enum
        WHERE enumlabel = '{ERROR}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""))
    op.execute(text(f"""DELETE FROM pg_enum
        WHERE enumlabel = '{DELETE_COMPLETE}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""))
    # op.execute(
    #     text(
    #         f"""DELETE FROM pg_enum
    #     WHERE enumlabel = '{RECOVER_ONGOING}'
    #     AND enumtypid = (
    #         SELECT oid FROM pg_type WHERE typname = '{enum_name}'
    #     )"""
    #     )
    # )
    op.execute(text(f"""DELETE FROM pg_enum
        WHERE enumlabel = '{PURGE_ONGOING}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
        )"""))
    op.drop_column("vfolders", "status_history")
