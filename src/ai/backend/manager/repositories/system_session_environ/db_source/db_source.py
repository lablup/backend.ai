from __future__ import annotations

from collections.abc import Sequence

from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.system_session_environ.scopes import (
    SessionSystemSessionEnvironScope,
)
from ai.backend.manager.models.system_session_environ.searchers import (
    SystemSessionEnvironSearcher,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("SystemSessionEnvironDBSource",)


class SystemSessionEnvironDBSource:
    _v2_ops: V2DBOpsProvider

    def __init__(self, v2_ops_provider: V2DBOpsProvider) -> None:
        self._v2_ops = v2_ops_provider

    async def search_at_scopes(
        self,
        scopes: Sequence[SessionSystemSessionEnvironScope],
    ) -> list[SystemSessionEnvironData]:
        searcher = SystemSessionEnvironSearcher(pagination=NoPagination(), conditions=[])
        async with self._v2_ops.read_ops() as r:
            result = await r.search_with_scopes(scopes, searcher)
        return result.items
