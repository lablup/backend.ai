"""detail_vfolder_deletion_status

Revision ID: 7ff52ff68bfc
Revises: a5319bfc7d7c
Create Date: 2024-02-06 15:27:34.975504

"""

import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.sql import text

from ai.backend.manager.models.base import EnumValueType, IDColumn, metadata

# revision identifiers, used by Alembic.
revision = "7ff52ff68bfc"
down_revision = "a5319bfc7d7c"
branch_labels = None
depends_on = None


BATCH_SIZE = 100

ENUM_NAME = "vfolderoperationstatus"


class VFolderOperationStatus(enum.StrEnum):
    # New enum values
    DELETE_PENDING = "delete-pending"  # vfolder is in trash bin
    DELETE_COMPLETE = "delete-complete"  # vfolder is deleted permanently, only DB row remains
    DELETE_ERROR = "delete-error"

    # Legacy enum values
    LEGACY_DELETE_COMPLETE = "deleted-complete"
    PURGE_ONGOING = "purge-ongoing"

    # Original enum values
    DELETE_ONGOING = "delete-ongoing"  # vfolder is being deleted in storage
    ERROR = "error"


vfolders = sa.Table(
    "vfolders",
    metadata,
    IDColumn("id"),
    sa.Column(
        "status",
        EnumValueType(VFolderOperationStatus),
        nullable=False,
    ),
    sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null()),
    extend_existing=True,
)


def add_enum(enum_val: VFolderOperationStatus) -> None:
    op.execute(f"ALTER TYPE {ENUM_NAME} ADD VALUE IF NOT EXISTS '{str(enum_val)}'")


def delete_enum(enum_val: VFolderOperationStatus) -> None:
    op.execute(
        text(
            f"""DELETE FROM pg_enum
        WHERE enumlabel = '{str(enum_val)}'
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = '{ENUM_NAME}'
        )"""
        )
    )


def update_legacy_to_new(
    conn,
    vfolder_t,
    legacy_enum: VFolderOperationStatus,
    new_enum: VFolderOperationStatus,
    *,
    legacy_enum_name: str | None = None,
    new_enum_name: str | None = None,
) -> None:
    _legacy_enum_name = legacy_enum_name or legacy_enum.name
    _new_enum_name = new_enum_name or new_enum.name

    while True:
        stmt = (
            sa.select([vfolder_t.c.id])
            .where(
                (vfolder_t.c.status == legacy_enum)
                | (vfolder_t.c.status_history.has_key(_legacy_enum_name))
            )
            .limit(BATCH_SIZE)
        )
        result = conn.execute(stmt).fetchall()
        vfolder_ids = [vf[0] for vf in result]

        if not vfolder_ids:
            break

        # Update `status`
        update_status = (
            sa.update(vfolder_t)
            .values({"status": new_enum})
            .where((vfolder_t.c.id.in_(vfolder_ids)) & (vfolder_t.c.status == legacy_enum))
        )
        conn.execute(update_status)

        # Update `status_history`
        update_status_history = (
            sa.update(vfolder_t)
            .values({
                "status_history": sa.func.jsonb_build_object(
                    _new_enum_name, vfolder_t.c.status_history.op("->>")(_legacy_enum_name)
                )
                + vfolder_t.c.status_history.op("-")(_legacy_enum_name)
            })
            .where(
                (vfolder_t.c.id.in_(vfolder_ids))
                & (vfolder_t.c.status_history.has_key(_legacy_enum_name))
            )
        )
        conn.execute(update_status_history)


def upgrade() -> None:
    conn = op.get_bind()

    add_enum(VFolderOperationStatus.DELETE_PENDING)
    add_enum(VFolderOperationStatus.DELETE_COMPLETE)
    add_enum(VFolderOperationStatus.DELETE_ERROR)
    conn.commit()

    vfolders = sa.Table(
        "vfolders",
        metadata,
        IDColumn("id"),
        sa.Column(
            "status",
            EnumValueType(VFolderOperationStatus),
            nullable=False,
        ),
        sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null()),
        extend_existing=True,
    )

    update_legacy_to_new(
        conn, vfolders, VFolderOperationStatus.PURGE_ONGOING, VFolderOperationStatus.DELETE_ONGOING
    )
    update_legacy_to_new(
        conn,
        vfolders,
        VFolderOperationStatus.LEGACY_DELETE_COMPLETE,
        VFolderOperationStatus.DELETE_PENDING,
        legacy_enum_name="DELETE_COMPLETE",
    )

    delete_enum(VFolderOperationStatus.LEGACY_DELETE_COMPLETE)
    delete_enum(VFolderOperationStatus.PURGE_ONGOING)

    op.add_column(
        "vfolders", sa.Column("status_changed", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        op.f("ix_vfolders_status_changed"), "vfolders", ["status_changed"], unique=False
    )
    conn.commit()


def downgrade() -> None:
    conn = op.get_bind()

    add_enum(VFolderOperationStatus.LEGACY_DELETE_COMPLETE)
    add_enum(VFolderOperationStatus.PURGE_ONGOING)
    conn.commit()

    vfolders = sa.Table(
        "vfolders",
        metadata,
        IDColumn("id"),
        sa.Column(
            "status",
            EnumValueType(VFolderOperationStatus),
            nullable=False,
        ),
        sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null()),
        extend_existing=True,
    )

    update_legacy_to_new(
        conn, vfolders, VFolderOperationStatus.DELETE_COMPLETE, VFolderOperationStatus.PURGE_ONGOING
    )  # `deleted` vfolders are not in DB rows in this downgraded version
    update_legacy_to_new(
        conn, vfolders, VFolderOperationStatus.DELETE_ONGOING, VFolderOperationStatus.PURGE_ONGOING
    )
    update_legacy_to_new(
        conn, vfolders, VFolderOperationStatus.DELETE_ERROR, VFolderOperationStatus.ERROR
    )
    update_legacy_to_new(
        conn,
        vfolders,
        VFolderOperationStatus.DELETE_PENDING,
        VFolderOperationStatus.LEGACY_DELETE_COMPLETE,
        new_enum_name="DELETE_COMPLETE",
    )

    delete_enum(VFolderOperationStatus.DELETE_PENDING)
    delete_enum(VFolderOperationStatus.DELETE_COMPLETE)
    delete_enum(VFolderOperationStatus.DELETE_ERROR)

    op.drop_index(op.f("ix_vfolders_status_changed"), table_name="vfolders")
    op.drop_column("vfolders", "status_changed")

    conn.commit()
