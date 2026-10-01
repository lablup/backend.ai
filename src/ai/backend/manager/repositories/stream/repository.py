from ai.backend.common.types import SessionId
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.stream.db_source.db_source import StreamDBSource


class StreamRepository:
    _db_source: StreamDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = StreamDBSource(db)

    async def get_streaming_session(self, session_id: SessionId) -> SessionRow:
        return await self._db_source.get_streaming_session(session_id)

    async def get_streaming_main_kernel(self, session_id: SessionId) -> KernelInfo:
        return await self._db_source.get_streaming_main_kernel(session_id)
