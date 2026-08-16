"""Global writes of the v2 ops: system-wide state outside the scope
hierarchy. Plain row writes — nothing becomes a scope and nothing is joined."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.upserter import GlobalEntityUpserter
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2GlobalWriteOps(V2WriteOpsBase):
    """Global writes, bound to a single session."""

    async def create_global_entity[TRow: Base, TData](
        self, creator: GlobalEntityCreator[TRow, TData]
    ) -> TData:
        """Insert one row of a global entity."""
        row = creator.build_row()
        await self._insert_row(row, creator.integrity_error_checks())
        return creator.to_data(row)

    async def atomic_create_global_entities[TRow: Base, TData](
        self, creators: Sequence[GlobalEntityCreator[TRow, TData]]
    ) -> list[TData]:
        """Insert global rows atomically in one flush; nothing is registered."""
        if not creators:
            return []
        rows = [creator.build_row() for creator in creators]
        self._sess.add_all(rows)
        try:
            await self._sess.flush()
        except sa.exc.IntegrityError as e:
            # Use first creator's checks (all specs share the same creator subclass)
            self._match_integrity_error(
                self._parse_integrity_error(e), creators[0].integrity_error_checks()
            )
        return [creator.to_data(row) for creator, row in zip(creators, rows, strict=True)]

    async def upsert_global_entity[TRow: Base, TData](
        self, upserter: GlobalEntityUpserter[TRow, TData]
    ) -> TData:
        """Insert or update on conflict, for a global entity."""
        row = await self._upsert_row_returning(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(),
            upserter.build_update_values(),
            upserter.integrity_error_checks(),
        )
        return upserter.to_data(row)
