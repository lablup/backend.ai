from __future__ import annotations

from collections.abc import Collection

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.system_session_environ.conditions import (
    SystemSessionEnvironConditions,
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
        domain_ids: Collection[DomainID],
        project_ids: Collection[ProjectID],
    ) -> list[SystemSessionEnvironData]:
        searcher = SystemSessionEnvironSearcher(
            pagination=NoPagination(),
            conditions=[
                SystemSessionEnvironConditions.at_global_or_scopes(domain_ids, project_ids)
            ],
        )
        async with self._v2_ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        return result.items
