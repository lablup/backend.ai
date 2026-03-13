from ai.backend.common.types import AccessKey
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class StreamDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_streaming_session(
        self,
        session_name: str,
        access_key: AccessKey,
    ) -> SessionRow:
        async with self._db.begin_readonly_session() as db_sess:
            return await SessionRow.get_session(
                db_sess,
                session_name,
                access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
