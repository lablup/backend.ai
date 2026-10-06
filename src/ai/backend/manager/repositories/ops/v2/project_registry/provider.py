from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.project_registry.read import ProjectRegistryReadOps
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class ProjectRegistryOpsProvider(V2DBOpsProvider):
    @asynccontextmanager
    @override
    async def read_ops(self) -> AsyncGenerator[ProjectRegistryReadOps]:
        async with self._db.begin_readonly_session_read_committed() as session:
            yield ProjectRegistryReadOps(session)
