from __future__ import annotations

from collections.abc import Collection

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.system_session_environ.db_source.db_source import (
    SystemSessionEnvironDBSource,
)

__all__ = ("SystemSessionEnvironRepository",)


class SystemSessionEnvironRepository:
    _db_source: SystemSessionEnvironDBSource

    def __init__(self, v2_ops_provider: V2DBOpsProvider) -> None:
        self._db_source = SystemSessionEnvironDBSource(v2_ops_provider)

    async def search_at_scopes(
        self,
        domain_ids: Collection[DomainID],
        project_ids: Collection[ProjectID],
    ) -> list[SystemSessionEnvironData]:
        """The rows at the global scope and at any of the given domains and projects."""
        return await self._db_source.search_at_scopes(domain_ids, project_ids)
