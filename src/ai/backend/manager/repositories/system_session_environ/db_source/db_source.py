from __future__ import annotations

from collections.abc import Sequence

from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.system_session_environ.creators import (
    SystemSessionEnvironCreator,
)
from ai.backend.manager.models.system_session_environ.scopes import (
    SessionSystemSessionEnvironScope,
)
from ai.backend.manager.models.system_session_environ.searchers import (
    SystemSessionEnvironSearcher,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("SystemSessionEnvironDBSource",)


class SystemSessionEnvironDBSource:
    _ops_provider: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops_provider = ops_provider

    async def search_in_scopes(
        self,
        scopes: Sequence[SessionSystemSessionEnvironScope],
        searcher: SystemSessionEnvironSearcher,
    ) -> list[SystemSessionEnvironData]:
        async with self._ops_provider.read_ops() as r:
            result = await r.search_with_scopes(scopes, searcher)
        return list(result.items)

    async def create(self, creator: SystemSessionEnvironCreator) -> SystemSessionEnvironData:
        async with self._ops_provider.write_ops() as w:
            return await w.create_entity(creator)
