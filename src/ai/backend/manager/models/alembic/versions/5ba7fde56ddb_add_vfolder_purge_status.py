"""add_vfolder_purge_status

Revision ID: 5ba7fde56ddb
Revises: 85615e005fa3
Create Date: 2023-09-19 16:29:20.893345

"""

from typing import cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import text

from ai.backend.manager.models.base import GUID, convention

# revision identifiers, used by Alembic.
revision = "5ba7fde56ddb"
down_revision = "85615e005fa3"
branch_labels = None
depends_on = None


DELETING = "deleting"
ERROR = "error"
DELETE_ONGOING = "delete-ongoing"  # vfolder is moving to trash bin
DELETE_COMPLETE = "deleted-complete"  # vfolder is in trash bin
# RECOVER_ONGOING = "recover-ongoing"  # vfolder is being recovered from trash bin
PURGE_ONGOING = "purge-ongoing"  # vfolder is being removed from trash bin


def upgrade():
    connection = op.get_bind()
    result = connection.execute(
        text(
            "SELECT t.typname as enum_name FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid GROUP BY enum_name;"
        )
    )
    enum_name = "vfolderoperationstatus"
    for row in result:
        try:
            candidate_enum = cast(str, row[0])
        except IndexError:
            continue
        if candidate_enum == "vfolderoperationstatus":
            break
        elif candidate_enum == "vfolderstatus":
            enum_name = candidate_enum
            break

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

    op.execute(f"ALTER TYPE vfolderoperationstatus RENAME VALUE '{DELETE_ONGOING}' TO '{DELETING}'")

    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{ERROR}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = 'vfolderoperationstatus'
        )"""
        )
    )
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{DELETE_COMPLETE}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = 'vfolderoperationstatus'
        )"""
        )
    )
    # op.execute(
    #     text(
    #         f"""DELETE FROM pg_enum
    #     WHERE enumlabel = '{RECOVER_ONGOING}'
    #     AND enumtypid = (
    #         SELECT oid FROM pg_type WHERE typname = 'vfolderoperationstatus'
    #     )"""
    #     )
    # )
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{PURGE_ONGOING}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = 'vfolderoperationstatus'
        )"""
        )
    )
    op.drop_column("vfolders", "status_history")
