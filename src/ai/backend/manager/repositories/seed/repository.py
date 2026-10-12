"""Seed item writes: every item of a run in one transaction, one savepoint per item."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite, SeedWriteItemResult


class SeedRepository:
    _ops: SeedOpsProvider

    def __init__(self, ops_provider: SeedOpsProvider) -> None:
        self._ops = ops_provider

    async def partial_write(
        self, writes: Sequence[SeedWrite], overwrite: bool
    ) -> list[SeedWriteItemResult]:
        """Write the items in the order given, answering for each. An entity or field row
        is inserted unless a row holds its key, or upserted under ``overwrite``."""
        async with self._ops.write_ops() as w:
            return await w.partial_write_seed_items(writes, overwrite)
