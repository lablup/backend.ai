"""Global writes of the v2 ops: system-wide state outside the scope
hierarchy. Plain row writes — nothing becomes a scope and nothing is joined."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.upserter import GlobalEntityUpserter
from ai.backend.manager.repositories.ops.v2.graph_write import V2GraphWriteOpsBase


class V2GlobalWriteOps(V2GraphWriteOpsBase):
    """Global writes, bound to a single session."""

    async def create_global_entity[TRow: Base, TData](
        self, creator: GlobalEntityCreator[TRow, TData]
    ) -> TData:
        """Insert one global entity row and provision it in the RBAC graph; it joins
        nothing."""
        row = creator.build_row()
        await self._insert_row(row, creator.integrity_error_checks())
        await self._provision([creator.entity_id(row)])
        return creator.to_data(row)

    async def atomic_create_global_entities[TRow: Base, TData](
        self, creators: Sequence[GlobalEntityCreator[TRow, TData]]
    ) -> list[TData]:
        """Insert global rows atomically in one flush, provisioning each as
        :meth:`create_global_entity` does for one."""
        if not creators:
            return []
        rows = [creator.build_row() for creator in creators]
        # First creator's checks: all specs share the same creator subclass.
        await self._insert_rows(rows, creators[0].integrity_error_checks())
        await self._provision([
            creator.entity_id(row) for creator, row in zip(creators, rows, strict=True)
        ])
        return [creator.to_data(row) for creator, row in zip(creators, rows, strict=True)]

    async def atomic_upsert_global_entities[TRow: Base, TData](
        self, upserters: Sequence[GlobalEntityUpserter[TRow, TData]]
    ) -> list[TData]:
        """Insert-or-update every global row atomically, provisioning each as
        :meth:`upsert_global_entity` does for one.

        One statement per row: each carries its own update values, so they cannot be
        folded into a single insert the way :meth:`atomic_create_global_entities` folds
        its rows.
        """
        if not upserters:
            return []
        rows = [
            await self._upsert_row_returning(
                upserter.row_class(),
                upserter.index_elements(),
                upserter.build_insert_values(),
                upserter.build_update_values(),
                upserter.integrity_error_checks(),
            )
            for upserter in upserters
        ]
        await self._provision([
            upserter.entity_id(row) for upserter, row in zip(upserters, rows, strict=True)
        ])
        return [upserter.to_data(row) for upserter, row in zip(upserters, rows, strict=True)]

    async def upsert_global_entity[TRow: Base, TData](
        self, upserter: GlobalEntityUpserter[TRow, TData]
    ) -> TData:
        """Insert or update on conflict, for a global entity; the node stays
        provisioned idempotently."""
        row = await self._upsert_row_returning(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(),
            upserter.build_update_values(),
            upserter.integrity_error_checks(),
        )
        await self._provision([upserter.entity_id(row)])
        return upserter.to_data(row)
