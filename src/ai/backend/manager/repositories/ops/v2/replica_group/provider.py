"""Replica-group DB ops provider.

Hands out the reconcile-side reads on both surfaces, so a tick reads its counts,
its history and its ``now`` in the transaction it writes in.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.ops.v2.replica_group.read import ReplicaGroupReadOps
from ai.backend.manager.repositories.ops.v2.replica_group.write import ReplicaGroupWriteOps


class ReplicaGroupOpsProvider(ReconcileOpsProvider):
    """Hands out :class:`ReplicaGroupReadOps` / :class:`ReplicaGroupWriteOps`."""

    @asynccontextmanager
    @override
    async def read_ops(self) -> AsyncGenerator[ReplicaGroupReadOps]:
        """Open a read-only transaction and yield the replica-group read ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield ReplicaGroupReadOps(sess)

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[ReplicaGroupWriteOps]:
        """Open a read-write transaction and yield the replica-group write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield ReplicaGroupWriteOps(sess)
