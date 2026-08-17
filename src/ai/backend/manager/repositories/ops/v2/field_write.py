"""Field writes of the v2 ops: rows owned by another entity, authorized
through the owner. Plain row writes — nothing becomes a scope and nothing is
joined."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.manager.actions.v2.ops.result import BulkFieldOpsResult
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.purger import FieldPurger
from ai.backend.manager.models.specs.upserter import FieldUpserter
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2FieldWriteOps(V2WriteOpsBase):
    """Field writes, bound to a single session."""

    async def create_field_entity[TOwnerID: EntityIdentifier, TRow: Base, TData](
        self, owner_id: TOwnerID, creator: FieldCreator[TOwnerID, TRow, TData]
    ) -> TData:
        """Insert one field row under its owner's settled identifier."""
        row = creator.build_row(owner_id)
        await self._insert_row(row, creator.integrity_error_checks())
        return creator.to_data(row)

    async def atomic_create_field_entities[TOwnerID: EntityIdentifier, TRow: Base, TData](
        self, owner_id: TOwnerID, creators: Sequence[FieldCreator[TOwnerID, TRow, TData]]
    ) -> list[TData]:
        """Insert field rows sharing one owner, atomically in a single flush."""
        if not creators:
            return []
        rows = [creator.build_row(owner_id) for creator in creators]
        self._sess.add_all(rows)
        try:
            await self._sess.flush()
        except sa.exc.IntegrityError as e:
            # Use first creator's checks (all specs share the same creator subclass)
            self._match_integrity_error(
                self._parse_integrity_error(e), creators[0].integrity_error_checks()
            )
        return [creator.to_data(row) for creator, row in zip(creators, rows, strict=True)]

    async def purge_field_entity[TRow: Base, TData](
        self, purger: FieldPurger[TRow, TData]
    ) -> TData | None:
        """Delete one field row; ``None`` if already gone. The delete is
        authorized through the owner."""
        await self._validate_conflict_checks(purger.conflict_checks())
        row = await self._delete_row_returning(purger.row_class(), purger.pk_value())
        if row is None:
            return None
        return purger.to_data(row)

    async def partial_bulk_purge_field_entities[TRow: Base, TData](
        self, purgers: Mapping[FieldIdentifier, FieldPurger[TRow, TData]]
    ) -> BulkFieldOpsResult[TData]:
        """Delete each named field row independently in its own savepoint; a
        missing row is answered with :class:`EntityNotFoundError` rather than
        skipped. Authorized through the owner, like the single field purge."""
        successes: dict[FieldIdentifier, TData] = {}
        errors: dict[FieldIdentifier, Exception] = {}
        for field_id, purger in purgers.items():
            try:
                async with self._sess.begin_nested():
                    data = await self.purge_field_entity(purger)
                    if data is None:
                        raise EntityNotFoundError(
                            f"{purger.row_class().__name__} {purger.pk_value()} not found"
                        )
                    successes[field_id] = data
            except Exception as e:
                errors[field_id] = e
        return BulkFieldOpsResult(successes=successes, errors=errors)

    async def upsert_field_entity[TOwnerID: EntityIdentifier, TRow: Base, TData](
        self, owner_id: TOwnerID, upserter: FieldUpserter[TOwnerID, TRow, TData]
    ) -> TData:
        """Insert or update a field row on conflict, under the owner's settled
        identifier."""
        row = await self._upsert_row_returning(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(owner_id),
            upserter.build_update_values(),
            upserter.integrity_error_checks(),
        )
        return upserter.to_data(row)
