import uuid

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.events.db_source.db_source import EventsDBSource


class EventsRepository:
    _db_source: EventsDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = EventsDBSource(db)

    async def match_sessions_by_name(
        self,
        session_name: str,
        access_key: AccessKey,
    ) -> list[SessionRow]:
        return await self._db_source.match_sessions_by_name(session_name, access_key)

    async def resolve_group_id(self, group_name: str) -> uuid.UUID:
        return await self._db_source.resolve_group_id(group_name)
