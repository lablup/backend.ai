"""Every write path a seed may take, in one session.

A seed reaches the database through the manager's own ops, and different rows want
different ones: a user is provisioned by the user ops, a share by the share ops, a
plain entity by the write ops under both. Composing them here means a scenario that
lays a user and a folder in one situation still writes them in one transaction.

Scenarios do not name this. The seeder holds it, and a table only names write specs.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.write import V2RelationWriteOps
from ai.backend.manager.repositories.ops.v2.share.write import V2ShareWriteOps
from ai.backend.manager.repositories.ops.v2.user.write import V2UserWriteOps


class SeedOps(V2UserWriteOps, V2ShareWriteOps, V2RelationWriteOps):
    """The write ops a seed may reach, composed."""


class SeedOpsProvider(V2DBOpsProvider):
    """Hands out :class:`SeedOps` bound to one read-write transaction."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[SeedOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield SeedOps(sess)
