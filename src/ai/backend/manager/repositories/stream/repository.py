from ai.backend.common.types import AccessKey
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
        access_key: AccessKey,
    ) -> SessionRow:
        return await self._db_source.get_streaming_session(session_name, access_key)
