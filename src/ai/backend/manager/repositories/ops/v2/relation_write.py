"""Relation writes of the v2 ops: rows that link two entities.

Every method names the pair rather than a row id — that is what a caller holds, and a
relation row's id never leaves the layer that wrote it. Nothing here touches the RBAC
graph: a relation is what business logic reads, not a fact about access.

Design rationale: `proposals/BEP-1075-entity-relation-operations.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
)
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2RelationWriteOps(V2WriteOpsBase):
    """Writes over the rows linking two entities, bound to a single session."""

    async def create_relation[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        creator: RelationCreator[TRow],
    ) -> bool:
        """Link the two entities, answering whether this call is what linked them.

        A pair that is already taken is settled by the spec: left alone, or written over
        to revive a relation that was switched off.
        """
        row = creator.build_row(left, right)
        row_class = creator.row_class()
        table = row_class.__table__
        column_keys = {c.key for c in sa.inspect(row_class).columns}
        values = {k: v for k, v in row.__dict__.items() if k in column_keys}
        stmt = pg_insert(table).values(values)
        conflict_values = creator.build_conflict_values()
        if conflict_values is None:
            stmt = stmt.on_conflict_do_nothing(index_elements=creator.index_elements())
        else:
            stmt = stmt.on_conflict_do_update(
                index_elements=creator.index_elements(), set_=conflict_values
            )
        try:
            result = await self._sess.execute(stmt.returning(*table.primary_key.columns))
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(
                self._parse_integrity_error(e), creator.integrity_error_checks()
            )
        await self._sess.flush()
        return result.first() is not None

    async def delete_relation[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[TRow],
    ) -> bool:
        """Switch the relation off, answering whether a row was there to switch."""
        return await self._write_relation_lifecycle(left, right, updater)

    async def restore_relation[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[TRow],
    ) -> bool:
        """Switch the relation back on, answering whether a row was there to switch.

        The reverse of :meth:`delete_relation` and a separate method for the same reason
        the entity soft delete and restore are: the operation an action declares is what
        RBAC checks and what the audit row records, and the two must not be one call
        that takes the direction as a value.
        """
        return await self._write_relation_lifecycle(left, right, updater)

    async def purge_relation[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        purger: RelationPurger[TRow],
    ) -> bool:
        """Remove the row linking the two entities, answering whether one went."""
        await self._validate_conflict_checks(purger.conflict_checks())
        row_class = purger.row_class()
        table = row_class.__table__
        stmt = sa.delete(table).where(self._relation_clause(purger.conditions(left, right)))
        result = await self._sess.execute(stmt.returning(*table.primary_key.columns))
        await self._sess.flush()
        return result.first() is not None

    async def _write_relation_lifecycle[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[TRow],
    ) -> bool:
        table = updater.row_class().__table__
        stmt = (
            sa.update(table)
            .values(updater.build_values())
            .where(self._relation_clause(updater.conditions(left, right)))
        )
        result = await self._sess.execute(stmt.returning(*table.primary_key.columns))
        await self._sess.flush()
        return result.first() is not None

    def _relation_clause(
        self, conditions: Sequence[QueryCondition]
    ) -> sa.sql.expression.ColumnElement[bool]:
        """AND the spec's conditions; an empty declaration would name every row, so it
        is refused rather than executed."""
        if not conditions:
            raise ValueError("a relation spec must name the pair with at least one condition")
        return sa.and_(*[condition() for condition in conditions])
