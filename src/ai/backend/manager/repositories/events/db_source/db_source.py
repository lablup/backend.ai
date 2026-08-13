import uuid

import sqlalchemy as sa

from ai.backend.common.types import AccessKey
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class EventsDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def match_sessions_by_name(
        self,
        session_name: str,
        access_key: AccessKey,
    ) -> list[SessionRow]:
        # The SSE stream is scoped by the owner_access_key wire parameter and
        # its event filter matches on access_key, so this lookup stays
        # keypair-scoped unlike the user-scoped SessionRow.match_sessions.
        async with self._db.begin_readonly_session(isolation_level="READ COMMITTED") as db_sess:
            query = (
                sa.select(SessionRow)
                .where((SessionRow.name == session_name) & (SessionRow.access_key == access_key))
                .order_by(sa.desc(SessionRow.created_at))
                .limit(10)
            )
            return list((await db_sess.scalars(query)).all())

    async def resolve_group_id(self, group_name: str) -> uuid.UUID:
        async with self._db.begin_readonly(isolation_level="READ COMMITTED") as conn:
            result = await conn.execute(
                sa.select(groups.c.id).select_from(groups).where(groups.c.name == group_name)
            )
            row = result.first()
            if row is None:
                raise ProjectNotFound
            return uuid.UUID(row.id)
