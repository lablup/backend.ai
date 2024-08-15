"""update kernels.vfolder_mounts.vfid structure

Revision ID: 9e599b62f6f1
Revises: a9eb2b002330
Create Date: 2023-06-22 20:57:16.726624

"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.expression import bindparam

from ai.backend.manager.models.base import IDColumn, SessionIDColumnType, convention

# revision identifiers, used by Alembic.
revision = "9e599b62f6f1"
down_revision = "a9eb2b002330"
branch_labels = None
depends_on = None

metadata = sa.MetaData(naming_convention=convention)
sessions = sa.Table(
    "sessions",
    metadata,
    IDColumn("id"),
    sa.Column("vfolder_mounts", postgresql.JSONB, nullable=True),
)
kernels = sa.Table(
    "kernels",
    metadata,
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
vfolders = sa.Table(
    "vfolders",
    metadata,
    IDColumn("id"),
    sa.Column("quota_scope_id", sa.String(length=64), nullable=False),
)


def list_chunk(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def upgrade() -> None:
    connection = op.get_bind()

    batch_size = 100
    known_quota_scopes: dict[UUID, str] = {}
    query = sa.select([sa.func.count()]).where(
        (sessions.c.vfolder_mounts != sa.cast(None, postgresql.JSONB))
        & (sa.func.jsonb_array_length(sessions.c.vfolder_mounts) > 0)
    )
    total_sessions = connection.execute(query).scalar()
    updated_count = 0

    def render_vfolder_id(old_vfid: str) -> str:
        if "/" in old_vfid and (old_vfid.startswith("user:") or old_vfid.startswith("project:")):
            return old_vfid

        if "/" in old_vfid:
            v2_id = old_vfid.split("/")[1]
        else:
            v2_id = old_vfid

        if quota_scope_id := known_quota_scopes.get(UUID(v2_id)):
            return f"{quota_scope_id}/{v2_id}"
        else:
            return v2_id

    prev_id = None
    while True:
        query = (
            sa.select([sessions.c.id, sa.cast(sessions.c.vfolder_mounts, postgresql.JSONB)])
            .order_by(sessions.c.id)
            .where(
                (sessions.c.vfolder_mounts != sa.cast(None, postgresql.JSONB))
                & (sa.func.jsonb_array_length(sessions.c.vfolder_mounts) > 0)
            )
            .limit(batch_size)
        )
        if prev_id:
            query = query.where(sessions.c.id > prev_id)
        rows = connection.execute(query).fetchall()
        if len(rows) == 0:
            break
        updates = []
        unknown_quota_scopes = set()

        for sess_id, vfolder_mounts in rows:
            for m in vfolder_mounts:
                v2_id = m["vfid"].split("/")[-1]
                if v2_id in known_quota_scopes:
                    continue
                unknown_quota_scopes.add(v2_id)

        query = sa.select([vfolders.c.id, vfolders.c.quota_scope_id]).where(
            vfolders.c.id.in_(unknown_quota_scopes)
        )
        result = connection.execute(query).fetchall()
        known_quota_scopes.update({row[0]: row[1] for row in result})

        for sess_id, vfolder_mounts in rows:
            new_mounts = [
                {
                    **mount,
                    "vfid": render_vfolder_id(mount["vfid"]),
                }
                for mount in vfolder_mounts
            ]
            updates.append({"row_id": sess_id, "vfolder_mounts": new_mounts})
        query = (
            sa.update(sessions)
            .values({"vfolder_mounts": bindparam("vfolder_mounts")})
            .where(sessions.c.id == bindparam("row_id"))
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
        updated_count += len(rows)
        print(f"Updated {updated_count} of {total_sessions} rows")
        prev_id = rows[-1][0]


def downgrade() -> None:
    connection = op.get_bind()

    batch_size = 100
    query = sa.select([sa.func.count()]).where(
        (sessions.c.vfolder_mounts != sa.cast(None, postgresql.JSONB))
        & (sa.func.jsonb_array_length(sessions.c.vfolder_mounts) > 0)
    )
    total_session = connection.execute(query).scalar()
    updated_count = 0
    prev_id = None
    while True:
        query = (
            sa.select([sessions.c.id, sa.cast(sessions.c.vfolder_mounts, postgresql.JSONB)])
            .order_by(sessions.c.id)
            .where(
                (sessions.c.vfolder_mounts != sa.cast(None, postgresql.JSONB))
                & (sa.func.jsonb_array_length(sessions.c.vfolder_mounts) > 0)
            )
            .limit(batch_size)
        )
        if prev_id:
            query = query.where(sessions.c.id > prev_id)
        rows = connection.execute(query).fetchall()
        if len(rows) == 0:
            break
        updates = []

        for sess_id, vfolder_mounts in rows:
            new_mounts = [
                {**mount, "vfid": mount["vfid"].split(":")[-1]} for mount in vfolder_mounts
            ]
            updates.append({"row_id": sess_id, "vfolder_mounts": new_mounts})

        query = (
            sa.update(sessions)
            .values({"vfolder_mounts": bindparam("vfolder_mounts")})
            .where(sessions.c.id == bindparam("row_id"))
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
        updated_count += len(rows)
        print(f"Updated {updated_count} of {total_session} rows")
        prev_id = rows[-1][0]
