from collections.abc import AsyncGenerator
from typing import Generic

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .session.creator import Creator
from .session.querier import Querier
from .session.updator import Updator
from .types import TBaseEntityData, TRow, TUpdator


class EngineWrapper(Generic[TRow, TBaseEntityData, TUpdator]):
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def begin_session(
        self,
    ) -> AsyncGenerator[
        tuple[Querier[TRow], Creator[TRow, TBaseEntityData], Updator[TUpdator]], None
    ]:
        async with self._db.begin_session() as session:
            querier = Querier[TRow](session)
            creator = Creator[TRow, TBaseEntityData](session)
            updator = Updator[TUpdator](session)
            yield querier, creator, updator

    async def begin_readonly_session(self) -> AsyncGenerator[Querier[TRow], None]:
        async with self._db.begin_readonly_session() as session:
            querier = Querier[TRow](session)
            yield querier
