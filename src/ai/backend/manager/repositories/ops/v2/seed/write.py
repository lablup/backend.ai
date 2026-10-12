"""Seed writes: each item's rows inserted unless a row holds their key, or upserted, one
savepoint per item."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.manager.errors.repository import RepositoryIntegrityError
from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite, SeedWriteItemResult
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class V2SeedWriteOps(V2WriteOps):
    """The v2 write ops plus the seed item write.

    A seed write leaves out the upserters' ``integrity_error_checks``: a violation stays a
    :class:`RepositoryIntegrityError`, so it fails its own item and no other.
    """

    async def partial_write_seed_items(
        self, writes: Sequence[SeedWrite], overwrite: bool
    ) -> list[SeedWriteItemResult]:
        """Write each item in its own savepoint, in the order given, so an item refused by
        a constraint leaves the rest written. Any other error raises."""
        results: list[SeedWriteItemResult] = []
        for write in writes:
            try:
                async with self._sess.begin_nested():
                    written = await self._write_seed_item(write, overwrite)
            except RepositoryIntegrityError as e:
                results.append(SeedWriteItemResult(written=False, error=e))
                continue
            results.append(SeedWriteItemResult(written=written))
        return results

    async def _write_seed_item(self, write: SeedWrite, overwrite: bool) -> bool:
        """Whether any row was written. A field row is written under an entity that was
        already there as well."""
        upserter = write.upserter
        row, written = await self._write_row(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(),
            upserter.build_update_values() if overwrite else None,
        )
        entity = upserter.entity_id(row)
        await self._provision([entity])
        await self._created_in(upserter.created_in(row), entity)
        if overwrite:
            for purger in write.field_purgers:
                await self.batch_purge_field_entities(entity, purger)
        for field_upserter in write.field_upserters:
            _, field_written = await self._write_row(
                field_upserter.row_class(),
                field_upserter.index_elements(),
                field_upserter.build_insert_values(entity),
                field_upserter.build_update_values() if overwrite else None,
            )
            written = written or field_written
        return written

    async def _write_row[TRow: Base](
        self,
        row_class: type[TRow],
        index_elements: list[str],
        insert_values: dict[str, Any],
        update_values: dict[str, Any] | None,
    ) -> tuple[TRow, bool]:
        """Insert the row, answering it and whether it was written. A row holding its
        ``index_elements`` is kept, or updated with ``update_values`` when given."""
        stmt = pg_insert(row_class).values(insert_values)
        if update_values is None:
            stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
        else:
            stmt = stmt.on_conflict_do_update(index_elements=index_elements, set_=update_values)
        try:
            row = (await self._sess.scalars(stmt.returning(row_class))).one_or_none()
        except sa.exc.IntegrityError as e:
            raise self._parse_integrity_error(e) from e
        if row is not None:
            return row, True
        existing = sa.select(row_class).where(
            *(getattr(row_class, column) == insert_values[column] for column in index_elements)
        )
        return (await self._sess.scalars(existing)).one(), False
