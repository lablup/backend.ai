"""Global-family writes of the v2 ops: system-wide state outside the scope
hierarchy. Plain row writes — nothing becomes a scope and nothing is joined."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import sqlalchemy as sa

from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import BulkResultWithFailures
from ai.backend.manager.models.specs.upserter import GlobalEntityUpserter
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2GlobalWriteOps(V2WriteOpsBase):
    """Writes of the global family, bound to a single session."""

    async def create_global_entity[TRow: Base, TData](
        self, creator: GlobalEntityCreator[TRow, TData]
    ) -> TData:
        """Insert one row of a global entity."""
        row = creator.build_row()
        await self._insert_row(row, creator.integrity_error_checks())
        return creator.to_data(row)

    async def bulk_create_global_entities[TRow: Base, TData](
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

    async def purge_global_entity[TRow: Base, TData](
        self, purger: GlobalEntityPurger[TRow, TData]
    ) -> TData | None:
        """Delete one row of a global entity; ``None`` if already gone."""
        await self._validate_conflict_checks(purger.conflict_checks())
        row = await self._delete_row_returning(purger.row_class(), purger.pk_value())
        if row is None:
            return None
        return purger.to_data(row)

    async def bulk_purge_global_entities[TRow: Base, TData](
        self, purgers: Mapping[EntityID, GlobalEntityPurger[TRow, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Delete each named global entity independently in its own savepoint; a
        missing row is answered with :class:`EntityNotFoundError` rather than
        skipped."""
        successes: dict[EntityID, TData] = {}
        errors: dict[EntityID, Exception] = {}
        for entity_id, purger in purgers.items():
            try:
                async with self._sess.begin_nested():
                    data = await self.purge_global_entity(purger)
                    if data is None:
                        raise EntityNotFoundError(
                            f"{purger.row_class().__name__} {purger.pk_value()} not found"
                        )
                    successes[entity_id] = data
            except Exception as e:
                errors[entity_id] = e
        return BulkResultWithFailures(successes=successes, errors=errors)

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
