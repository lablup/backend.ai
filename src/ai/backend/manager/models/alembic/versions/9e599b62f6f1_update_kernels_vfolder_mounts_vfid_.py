"""update kernels.vfolder_mounts.vfid structure

Revision ID: 9e599b62f6f1
Revises: 5fbd368d12a2
Create Date: 2023-06-22 20:57:16.726624

"""
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.expression import bindparam

from ai.backend.common.types import VFolderMount
from ai.backend.manager.models import SessionRow, kernels, vfolders
from ai.backend.manager.models.base import IDColumn, SessionIDColumnType, convention

# revision identifiers, used by Alembic.
revision = "9e599b62f6f1"
down_revision = "5fbd368d12a2"
branch_labels = None
depends_on = None


ZERO_FILLED_UUID = "00000000000000000000000000000000"


def list_chunk(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def upgrade():
    connection = op.get_bind()

    batch_size = 100
    known_quota_scopes: dict[UUID, str] = {}
    query = (
        sa.select([SessionRow.id])
        .order_by(SessionRow.id)
        .where(
            (SessionRow.vfolder_mounts != sa.cast(None, postgresql.JSONB))
            & (sa.func.jsonb_array_length(SessionRow.vfolder_mounts) > 0)
        )
    )
    result = connection.execute(query).fetchall()
    session_ids_to_update = [row[0] for row in result]
    updated_count = 0
    for session_ids in list_chunk(session_ids_to_update, batch_size):
        query = (
            sa.select([SessionRow.id, sa.cast(SessionRow.vfolder_mounts, postgresql.JSONB)])
            .order_by(SessionRow.id)
            .where(SessionRow.id.in_(session_ids))
        )
        rows = connection.execute(query).fetchall()
        updates = []
        unknown_quota_scopes = set()

        for sess_id, vfolder_mounts in rows:
            unknown_quota_scopes |= set(
                UUID(m["vfid"])
                for m in vfolder_mounts
                if (m["vfid"] not in known_quota_scopes and "/" not in m["vfid"])
            )
        query = sa.select([vfolders.c.id, vfolders.c.quota_scope_id]).where(
            vfolders.c.id.in_(unknown_quota_scopes)
        )
        result = connection.execute(query).fetchall()
        known_quota_scopes.update({row[0]: row[1] for row in result})

        for sess_id, vfolder_mounts in rows:
            new_mounts = [
                VFolderMount.from_json(
                    {
                        **mount,
                        "vfid": (
                            f"{known_quota_scopes.get(UUID(mount['vfid']), ZERO_FILLED_UUID)}/{mount['vfid']}"
                            if "/" not in mount["vfid"]
                            else mount["vfid"]
                        ),
                    }
                )
                for mount in vfolder_mounts
            ]
            updates.append({"row_id": sess_id, "vfolder_mounts": new_mounts})
        query = (
            sa.update(SessionRow)
            .values(vfolder_mounts=bindparam("vfolder_mounts"))
            .where(SessionRow.id == bindparam("row_id"))
        )
        connection.execute(
            query,
            updates,
        )
        query = (
            sa.update(kernels)
            .values(vfolder_mounts=bindparam("vfolder_mounts"))
            .where(kernels.c.session_id == bindparam("row_id"))
        )
        connection.execute(
            query,
            updates,
        )
        updated_count += len(session_ids)
        print(f"Updated {updated_count} of {len(session_ids_to_update)} rows")


def downgrade():
    connection = op.get_bind()

    batch_size = 100
    query = (
        sa.select([SessionRow.id])
        .order_by(SessionRow.id)
        .where(
            (SessionRow.vfolder_mounts != sa.cast(None, postgresql.JSONB))
            & (sa.func.jsonb_array_length(SessionRow.vfolder_mounts) > 0)
        )
    )
    result = connection.execute(query).fetchall()
    session_ids_to_update = [row[0] for row in result]
    updated_count = 0
    fake_meta = sa.MetaData(naming_convention=convention)
    fake_sessions = sa.Table(
        "sessions",
        fake_meta,
        IDColumn("id"),
        sa.Column("vfolder_mounts", postgresql.JSONB, nullable=True),
    )
    fake_kernels = sa.Table(
        "kernels",
        fake_meta,
        sa.Column(
            "session_id",
            SessionIDColumnType,
            sa.ForeignKey("sessions.id"),
            unique=False,
            index=True,
            nullable=False,
        ),
        sa.Column("vfolder_mounts", postgresql.JSONB, nullable=True),
    )
    for session_ids in list_chunk(session_ids_to_update, batch_size):
        query = (
            sa.select([SessionRow.id, sa.cast(SessionRow.vfolder_mounts, postgresql.JSONB)])
            .order_by(SessionRow.id)
            .where(SessionRow.id.in_(session_ids))
        )
        rows = connection.execute(query).fetchall()
        updates = []

        for sess_id, vfolder_mounts in rows:
            new_mounts = [
                {**mount, "vfid": mount["vfid"].split("/")[::-1][0]} for mount in vfolder_mounts
            ]
            updates.append({"row_id": sess_id, "vfolder_mounts": new_mounts})

        query = (
            sa.update(fake_sessions)
            .values({"vfolder_mounts": bindparam("vfolder_mounts")})
            .where(fake_sessions.c.id == bindparam("row_id"))
        )
        connection.execute(
            query,
            updates,
        )
        query = (
            sa.update(fake_kernels)
            .values(vfolder_mounts=bindparam("vfolder_mounts"))
            .where(fake_kernels.c.session_id == bindparam("row_id"))
        )
        connection.execute(
            query,
            updates,
        )
        updated_count += len(session_ids)
        print(f"Updated {updated_count} of {len(session_ids_to_update)} rows")
