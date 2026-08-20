"""Sidecar writes of the v2 ops: rows that ride beside the entity graph.

Plain row writes — nothing becomes a scope, nothing is joined, and no owner is
injected. What a row names of an entity is a value it records.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.creator import DanglingFieldCreator, NestedFieldCreator
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2DanglingFieldWriteOps(V2WriteOpsBase):
    """Sidecar writes, bound to a single session."""

    async def create_dangling_field[TRow: Base, TData](
        self, entity_type: EntityType, creator: DanglingFieldCreator[TRow, TData]
    ) -> TData:
        """Insert one row that names a kind and no owner."""
        row = creator.build_row(entity_type)
        await self._insert_row(row, creator.integrity_error_checks())
        return creator.to_data(row)

    async def atomic_create_dangling_fields[TRow: Base, TData](
        self, entity_type: EntityType, creators: Sequence[DanglingFieldCreator[TRow, TData]]
    ) -> list[TData]:
        """Insert such rows atomically in a single flush."""
        if not creators:
            return []
        rows = [creator.build_row(entity_type) for creator in creators]
        # First creator's checks: all specs share the same creator subclass.
        await self._insert_rows(rows, creators[0].integrity_error_checks())
        return [creator.to_data(row) for creator, row in zip(creators, rows, strict=True)]

    async def atomic_create_dangling_fields_with_nested[
        TRow: Base,
        TData,
        TFieldRow: Base,
        TFieldData,
    ](
        self,
        entity_type: EntityType,
        creators: Sequence[DanglingFieldCreator[TRow, TData]],
        field_creators: Sequence[NestedFieldCreator[Any, TFieldRow, TFieldData]],
    ) -> list[TData]:
        """Insert sidecar rows and the rows each of them owns, in one transaction.

        Every field spec is built under every row written, which is how a batch sharing
        one set of owned rows is expressed. The owner ids do not exist until the parents
        are written, so a failed field row takes the parents down with it.
        """
        if not creators:
            return []
        rows = [creator.build_row(entity_type) for creator in creators]
        await self._insert_rows(rows, creators[0].integrity_error_checks())
        if field_creators:
            owner_ids = [creator.field_id(row) for creator, row in zip(creators, rows, strict=True)]
            await self._insert_rows(
                [
                    field_creator.build_row(owner_id)
                    for owner_id in owner_ids
                    for field_creator in field_creators
                ],
                field_creators[0].integrity_error_checks(),
            )
        return [creator.to_data(row) for creator, row in zip(creators, rows, strict=True)]
