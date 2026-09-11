"""Relation writes: a row linking a scope to a target, and what each side reads.

A relation (a project and a resource group) is asymmetric in the graph. The scope
governs the target under a READ cap, so the scope's roles read the target and what
it owns (a resource group's agents, a registry's images). The target is only shared
the scope, under a READ cap, so the target's roles read the scope itself and nothing
the scope owns. The relation row is the domain's table; its shape comes from the spec (BEP-1075). Switching a relation off keeps both reads:
the pair stays listed on both sides until it is purged.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.actions.v2.ops.result import BulkRelationResult, RelationWriteResult
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
    RelationUpserter,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class V2RelationWriteOps(V2WriteOps):
    """The general write ops plus the relations between existing entities."""

    async def create_relations[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        creator: RelationCreator[TScope, TTarget, TRow],
        pairs: Sequence[tuple[TScope, TTarget]],
    ) -> list[bool]:
        """Link each pair: the relation row, the scope governing the target under READ,
        and READ on the scope added to what the target holds of it. Answers per pair, in
        the order given, whether the link was written.

        A pair already linked, switched off or not, is left as it stands and answered
        ``False`` — naming one twice is not something a caller has to avoid. Every other
        integrity failure is the spec's to map.

        Both entities are already in the graph: a node is written when the entity is
        created, so one missing is a broken state and not something a relation repairs.
        """
        for scope, target in pairs:
            await self._validate_precondition_checks(creator.precondition_checks(scope, target))
        written = [
            await self._insert_relation_row(
                creator.build_row(scope, target), creator.integrity_error_checks()
            )
            for scope, target in pairs
        ]
        linked = [pair for pair, is_new in zip(pairs, written, strict=True) if is_new]
        for scope, target in linked:
            await self._govern([scope], target, cap=Permission.READ)
            await self._widen_share(target, scope, {Permission.READ: None})
        return written

    async def _validate_precondition_checks(self, checks: Sequence[PreconditionCheck]) -> None:
        """Refuse the write where the spec named a row that must not be there. What the
        database cannot state for itself is stated here, each with its own error."""
        for check in checks:
            if (await self._sess.execute(check.finder)).first() is not None:
                raise check.error

    async def _insert_relation_row(self, row: Base, checks: Sequence[IntegrityErrorCheck]) -> bool:
        """Insert the relation row unless the pair already stands, answering whether it
        was written. The conflict is skipped in SQL, so a duplicate costs no savepoint
        and every other violation still reaches the spec's checks."""
        row_class = type(row)
        table = sa.inspect(row_class).local_table
        columns = {column.key for column in table.columns}
        values = {key: value for key, value in row.__dict__.items() if key in columns}
        primary_key = next(iter(table.primary_key))
        stmt = pg_insert(row_class).values(values).on_conflict_do_nothing().returning(primary_key)
        try:
            result = await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)
        return result.first() is not None

    async def delete_relations[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        updater: RelationLifecycleUpdater[TScope, TTarget, TRow],
        pairs: Sequence[tuple[TScope, TTarget]],
    ) -> list[bool]:
        """Switch each pair off, answering per pair, in the order given, whether the row
        moved. A pair already off, or standing in no relation at all, answers False."""
        return [await self._switch_relation(updater, scope, target) for scope, target in pairs]

    async def restore_relations[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        updater: RelationLifecycleUpdater[TScope, TTarget, TRow],
        pairs: Sequence[tuple[TScope, TTarget]],
    ) -> list[bool]:
        """Switch each pair back on, answering as :meth:`delete_relations` does."""
        return [await self._switch_relation(updater, scope, target) for scope, target in pairs]

    async def partial_upsert_relations[
        TScope: EntityIdentifier,
        TTarget: EntityIdentifier,
        TRow: Base,
    ](
        self,
        upserter: RelationUpserter[TScope, TTarget, TRow],
        pairs: Sequence[tuple[TScope, TTarget]],
    ) -> BulkRelationResult:
        """Write each pair's row in its own savepoint, inserting the pair that does not
        stand yet, so one refusing pair leaves the rest written and answers with why.

        The graph reads are registered for every pair, idempotently: a pair written
        again is already governed and already shared.
        """
        results: list[RelationWriteResult] = []
        for scope, target in pairs:
            try:
                async with self._sess.begin_nested():
                    await self._upsert_row_returning(
                        upserter.row_class(),
                        upserter.index_elements(),
                        upserter.build_insert_values(scope, target),
                        upserter.build_update_values(),
                        upserter.integrity_error_checks(),
                    )
                    await self._govern([scope], target, cap=Permission.READ)
                    await self._widen_share(target, scope, {Permission.READ: None})
                results.append(RelationWriteResult(scope=scope, target=target, written=True))
            except Exception as e:
                results.append(
                    RelationWriteResult(scope=scope, target=target, written=False, error=e)
                )
        return BulkRelationResult(results=results)

    async def partial_switch_relations[
        TScope: EntityIdentifier,
        TTarget: EntityIdentifier,
        TRow: Base,
    ](
        self,
        updater: RelationLifecycleUpdater[TScope, TTarget, TRow],
        pairs: Sequence[tuple[TScope, TTarget]],
    ) -> BulkRelationResult:
        """Switch each pair in its own savepoint, so one refusing pair leaves the rest
        written and answers with why.

        The plural switches above take the batch down together; this is for a caller
        that reports per pair. A pair standing in no relation is answered ``written``
        false with no error: there was nothing to switch.
        """
        results: list[RelationWriteResult] = []
        for scope, target in pairs:
            try:
                async with self._sess.begin_nested():
                    written = await self._switch_relation(updater, scope, target)
                results.append(RelationWriteResult(scope=scope, target=target, written=written))
            except Exception as e:
                results.append(
                    RelationWriteResult(scope=scope, target=target, written=False, error=e)
                )
        return BulkRelationResult(results=results)

    async def purge_relations[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        purger: RelationPurger[TScope, TTarget, TRow],
        pairs: Sequence[tuple[TScope, TTarget]],
    ) -> list[bool]:
        """Unlink each pair: the relation row and the govern go, READ on the scope is
        taken back from the target, and a share left with nothing goes too. Answers per
        pair, in the order given, whether it was linked; unlinking one that was not is
        silent."""
        await self._validate_conflict_checks(purger.conflict_checks())
        unlinked: list[bool] = []
        for scope, target in pairs:
            unlinked.append(await self._purge_one_relation(purger, scope, target))
        return unlinked

    async def _purge_one_relation[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self, purger: RelationPurger[TScope, TTarget, TRow], scope: TScope, target: TTarget
    ) -> bool:
        row_class = purger.row_class()
        stmt = sa.delete(row_class).returning(row_class)
        for condition in purger.conditions(scope, target):
            stmt = stmt.where(condition())
        if not (await self._sess.scalars(stmt)).all():
            return False
        await self._ungovern([scope], target)
        await self._narrow_share(target, scope, {Permission.READ: None})
        await self._unshare_if_empty(target, scope)
        return True

    async def _switch_relation[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        updater: RelationLifecycleUpdater[TScope, TTarget, TRow],
        scope: TScope,
        target: TTarget,
    ) -> bool:
        stmt = sa.update(updater.row_class()).values(updater.build_values())
        for condition in updater.conditions(scope, target):
            stmt = stmt.where(condition())
        stmt = stmt.returning(next(iter(sa.inspect(updater.row_class()).local_table.primary_key)))
        return (await self._sess.execute(stmt)).first() is not None

    async def _unshare_if_empty(self, scope: EntityIdentifier, entity: EntityIdentifier) -> None:
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id == self._node_id_query(scope),
                EntityMembershipRow.member_entity_id == self._node_id_query(entity),
                EntityMembershipRow.capped.is_(True),
                ~sa.exists().where(EntityMembershipCapRow.membership_id == EntityMembershipRow.id),
            )
        )
