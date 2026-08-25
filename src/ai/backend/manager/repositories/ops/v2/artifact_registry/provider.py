"""Artifact registry DB ops provider.

Hands out :class:`ArtifactRegistryWriteOps` where :class:`V2DBOpsProvider` hands out
the general write ops, so the registry pair primitive reaches a repository by
injection rather than by every repository inheriting it.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.artifact_registry.write import (
    ArtifactRegistryWriteOps,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class ArtifactRegistryOpsProvider(V2DBOpsProvider):
    """Hands out :class:`ArtifactRegistryWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[ArtifactRegistryWriteOps]:
        """Open a read-write transaction and yield the registry write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield ArtifactRegistryWriteOps(sess)
