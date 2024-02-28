"""detail_vfolder_deletion_status

Revision ID: 7ff52ff68bfc
Revises: a5319bfc7d7c
Create Date: 2024-02-06 15:27:34.975504

"""

import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "7ff52ff68bfc"
down_revision = "a5319bfc7d7c"
branch_labels = None
depends_on = None


class OldVFolderOperationStatus(enum.StrEnum):
    READY = "ready"
    PERFORMING = "performing"
    CLONING = "cloning"
    MOUNTED = "mounted"
    ERROR = "error"
    DELETE_ONGOING = "delete-ongoing"  # vfolder is being deleted
    DELETE_COMPLETE = "deleted-complete"  # vfolder is deleted
    PURGE_ONGOING = "purge-ongoing"  # vfolder is being removed permanently


def upgrade() -> None:
    conn = op.get_bind()
    # Relax the colum type from enum to varchar(64).
    conn.execute(
        text("ALTER TABLE vfolders ALTER COLUMN status TYPE varchar(64) USING status::text;")
    )
    conn.execute(text("ALTER TABLE vfolders ALTER COLUMN status SET DEFAULT 'ready';"))
    conn.execute(
        text(
            """\
        UPDATE vfolders
        SET status = CASE
            WHEN status = 'deleted-complete' THEN 'delete-pending'
            WHEN status = 'purge-ongoing' THEN 'delete-ongoing'
            WHEN status = 'error' THEN 'delete-error'
            ELSE status
        END,
        status_history = (
            SELECT jsonb_object_agg(new_key, value)
            FROM (
                SELECT
                    CASE
                        WHEN key = 'deleted-complete' THEN 'delete-pending'
                        WHEN key = 'purge-ongoing' THEN 'delete-ongoing'
                        WHEN key = 'error' THEN 'delete-error'
                        ELSE key
                    END AS new_key,
                    value
                FROM jsonb_each(status_history)
            ) AS subquery
        );
    """
        )
    )
    conn.execute(text("DROP TYPE vfolderoperationstatus;"))
    op.add_column(
        "vfolders",
        sa.Column(
            "status_changed",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_vfolders_status_changed"),
        "vfolders",
        ["status_changed"],
        unique=False,
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """\
        UPDATE vfolders
        SET status = CASE
            WHEN status = 'delete-pending' THEN 'deleted-complete'
            WHEN status = 'delete-complete' THEN 'purge-ongoing'
            WHEN status = 'delete-ongoing' THEN 'purge-ongoing'
            WHEN status = 'delete-error' THEN 'error'
            ELSE status
        END,
        status_history = (
            SELECT jsonb_object_agg(new_key, value)
            FROM (
                SELECT
                    CASE
                        WHEN key = 'delete-pending' THEN 'deleted-complete'
                        WHEN key = 'delete-complete' THEN 'purge-ongoing'
                        WHEN key = 'delete-ongoing' THEN 'purge-ongoing'
                        WHEN key = 'delete-error' THEN 'error'
                        ELSE key
                    END AS new_key,
                    value
                FROM jsonb_each(status_history)
            ) AS subquery
        );
    """
        )
    )
    conn.execute(
        text(
            "CREATE TYPE vfolderoperationstatus AS ENUM (%s)"
            % (",".join(f"'{choice.value}'" for choice in OldVFolderOperationStatus))
        )
    )
    conn.execute(text("ALTER TABLE vfolders ALTER COLUMN status DROP DEFAULT;"))
    conn.execute(
        text(
            "ALTER TABLE vfolders ALTER COLUMN status TYPE vfolderoperationstatus "
            "USING status::vfolderoperationstatus;"
        )
    )
    conn.execute(text("ALTER TABLE vfolders ALTER COLUMN status SET DEFAULT 'ready';"))
    op.drop_index(op.f("ix_vfolders_status_changed"), table_name="vfolders")
    op.drop_column("vfolders", "status_changed")
