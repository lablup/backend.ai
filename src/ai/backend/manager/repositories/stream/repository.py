import uuid

from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.stream.db_source.db_source import StreamDBSource


class StreamRepository:
    _db_source: StreamDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = StreamDBSource(db)

    async def get_streaming_session(
        self,
        session_name: str,
        user_uuid: uuid.UUID,
    ) -> SessionRow:
        return await self._db_source.get_streaming_session(session_name, user_uuid)
