import uuid

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.events.db_source.db_source import EventsDBSource


class EventsRepository:
    _db_source: EventsDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = EventsDBSource(db)

    async def resolve_group_id(self, group_name: str) -> uuid.UUID:
        return await self._db_source.resolve_group_id(group_name)
