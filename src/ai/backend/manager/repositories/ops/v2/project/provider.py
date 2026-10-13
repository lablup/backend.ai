from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.project.write import ProjectWriteOps
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class ProjectOpsProvider(V2DBOpsProvider):
    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[ProjectWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield ProjectWriteOps(sess)
