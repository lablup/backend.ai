import uuid

import sqlalchemy as sa

from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.project.row import groups
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class EventsDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def resolve_group_id(self, group_name: str) -> uuid.UUID:
        async with self._db.begin_readonly(isolation_level="READ COMMITTED") as conn:
            result = await conn.execute(
                sa.select(groups.c.id).select_from(groups).where(groups.c.name == group_name)
            )
            row = result.first()
            if row is None:
                raise ProjectNotFound
            return uuid.UUID(row.id)
