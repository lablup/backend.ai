from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class EngineWrapper:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def begin_session(self) -> AsyncGenerator[SASession, None]:
        async with self._db.begin_session() as session:
            yield session

    async def begin_readonly_session(self) -> AsyncGenerator[SASession, None]:
        async with self._db.begin_readonly_session() as session:
            yield session
