"""Seed writes: an upserter's row inserted unless a row already holds its key, or
upserted, one savepoint per item."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityIdentifier, FieldData
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import EntityInsertResult, IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter, FieldUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite, SeedWriteItemResult
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class V2SeedWriteOps(V2WriteOps):
    """The v2 write ops plus the insert that leaves an existing row as it is."""

    async def partial_write_seed_items(
        self, writes: Sequence[SeedWrite], overwrite: bool
    ) -> list[SeedWriteItemResult]:
        """Write each item in its own savepoint, in the order given, so an item refused by
        a unique or foreign key leaves the rest written. Any other error raises."""
        results: list[SeedWriteItemResult] = []
        for write in writes:
            try:
                async with self._sess.begin_nested():
                    written = await self._write_seed_item(write, overwrite)
            except (UniqueConstraintViolationError, ForeignKeyViolationError) as e:
                results.append(SeedWriteItemResult(written=False, error=e))
                continue
            results.append(SeedWriteItemResult(written=written))
        return results

    async def _write_seed_item(self, write: SeedWrite, overwrite: bool) -> bool:
        """Whether any row was written. A field row is written under an entity that was
        already there as well."""
        if overwrite:
            data = await self.upsert_entity(write.upserter)
            for purger in write.field_purgers:
                await self.batch_purge_field_entities(data.entity_id(), purger)
            await self.atomic_upsert_field_entities(data.entity_id(), write.field_upserters)
            return True
        entity = await self.insert_entity_if_absent(write.upserter)
        fields = await self.atomic_insert_field_entities_if_absent(
            entity.data.entity_id(), write.field_upserters
        )
        return entity.inserted or bool(fields)

    async def insert_entity_if_absent[TRow: Base, TData](
        self, upserter: EntityUpserter[TRow, TData]
    ) -> EntityInsertResult[TData]:
        """Insert the entity row unless a row holds its key, answering whichever row
        stands. The scope is provisioned idempotently either way, as the upsert does."""
        row, inserted = await self._insert_row_if_absent(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(),
            upserter.integrity_error_checks(),
        )
        entity = upserter.entity_id(row)
        await self._provision([entity])
        await self._created_in(upserter.created_in(row), entity)
        return EntityInsertResult(data=upserter.to_data(row), inserted=inserted)

    async def atomic_insert_field_entities_if_absent[
        TOwnerID: EntityIdentifier,
        TRow: Base,
        TData: FieldData,
    ](
        self, owner_id: TOwnerID, upserters: Sequence[FieldUpserter[TOwnerID, TRow, TData]]
    ) -> list[TData]:
        """Insert every field row of one owner that no row holds the key of yet,
        answering the rows inserted."""
        inserted_rows: list[TData] = []
        for upserter in upserters:
            row, inserted = await self._insert_row_if_absent(
                upserter.row_class(),
                upserter.index_elements(),
                upserter.build_insert_values(owner_id),
                upserter.integrity_error_checks(),
            )
            if inserted:
                inserted_rows.append(upserter.to_data(row))
        return inserted_rows

    async def _insert_row_if_absent[TRow: Base](
        self,
        row_class: type[TRow],
        index_elements: list[str],
        insert_values: dict[str, Any],
        checks: Sequence[IntegrityErrorCheck],
    ) -> tuple[TRow, bool]:
        """Insert the row unless one holds its ``index_elements``, answering the row and
        whether it was inserted. A conflict on any other unique key raises."""
        stmt = (
            pg_insert(row_class)
            .values(insert_values)
            .on_conflict_do_nothing(index_elements=index_elements)
            .returning(row_class)
        )
        try:
            row = (await self._sess.scalars(stmt)).one_or_none()
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)
        if row is not None:
            return row, True
        existing = sa.select(row_class).where(
            *(getattr(row_class, column) == insert_values[column] for column in index_elements)
        )
        return (await self._sess.scalars(existing)).one(), False
