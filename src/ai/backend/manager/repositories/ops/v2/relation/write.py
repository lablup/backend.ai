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
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class V2RelationWriteOps(V2WriteOps):
    """The general write ops plus the relations between existing entities."""

    async def create_relation[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self, creator: RelationCreator[TScope, TTarget, TRow], scope: TScope, target: TTarget
    ) -> None:
        """Link the scope to the target: the relation row, the scope governing the
        target under READ, and READ on the scope added to what the target holds of
        it. A pair already linked, switched off or not, is a unique violation the spec
        maps. What the spec refuses runs first, each with its own error."""
        for check in creator.precondition_checks(scope, target):
            if (await self._sess.execute(check.finder)).first() is not None:
                raise check.error
        await self._insert_row(creator.build_row(scope, target), creator.integrity_error_checks())
        await self._govern([scope], target, cap=Permission.READ)
        await self._widen_share(target, scope, {Permission.READ: None})

    async def purge_relation[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self, purger: RelationPurger[TScope, TTarget, TRow], scope: TScope, target: TTarget
    ) -> bool:
        """Unlink one pair. Kept for the same caller as :meth:`create_relation`."""
        await self._validate_conflict_checks(purger.conflict_checks())
        return await self._purge_one_relation(purger, scope, target)

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

    async def delete_relation[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        updater: RelationLifecycleUpdater[TScope, TTarget, TRow],
        scope: TScope,
        target: TTarget,
    ) -> None:
        """Switch the relation off: the lifecycle column alone. What each side reads
        of the other stays, so the relation is still listed and can be switched back."""
        await self._switch_relation(updater, scope, target)

    async def restore_relation[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        updater: RelationLifecycleUpdater[TScope, TTarget, TRow],
        scope: TScope,
        target: TTarget,
    ) -> None:
        """Switch the relation back on: the lifecycle column alone."""
        await self._switch_relation(updater, scope, target)

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
    ) -> None:
        stmt = sa.update(updater.row_class()).values(updater.build_values())
        for condition in updater.conditions(scope, target):
            stmt = stmt.where(condition())
        await self._sess.execute(stmt)

    async def _unshare_if_empty(self, scope: EntityIdentifier, entity: EntityIdentifier) -> None:
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id == self._node_id_query(scope),
                EntityMembershipRow.member_entity_id == self._node_id_query(entity),
                EntityMembershipRow.capped.is_(True),
                ~sa.exists().where(EntityMembershipCapRow.membership_id == EntityMembershipRow.id),
            )
        )
