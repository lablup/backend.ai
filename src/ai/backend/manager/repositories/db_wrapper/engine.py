from collections.abc import AsyncGenerator

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .session import SessionWrapper


class EngineWrapper:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def begin_session(self) -> AsyncGenerator[SessionWrapper, None]:
        async with self._db.begin_session() as session:
            yield SessionWrapper(session)

    async def begin_readonly_session(self) -> AsyncGenerator[SessionWrapper, None]:
        async with self._db.begin_readonly_session() as session:
            yield SessionWrapper(session)
