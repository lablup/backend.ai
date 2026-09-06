"""Relation writes: a row linking a scope to a target, and what each side reads.

A relation (a project and a resource group) is asymmetric in the graph. The scope
governs the target under a READ cap, so the scope's roles read the target and what
it owns (a resource group's agents, a registry's images). The target is only shared
the scope, under a READ cap, so the target's roles read the scope itself and nothing
the scope owns. The relation row is the domain's table; its shape comes from the spec (BEP-1075). Switching a relation off keeps both reads:
the pair stays listed on both sides until it is purged.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
)
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
        maps."""
        await self._insert_row(creator.build_row(scope, target), creator.integrity_error_checks())
        await self._govern([scope], target, cap=Permission.READ)
        await self._widen_share(target, scope, {Permission.READ: None})

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

    async def purge_relation[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self, purger: RelationPurger[TScope, TTarget, TRow], scope: TScope, target: TTarget
    ) -> bool:
        """Unlink the scope from the target: the relation row and the govern go, READ
        on the scope is taken back from the target, and a share left with nothing goes
        too. Answers whether the pair was linked; unlinking one that was not is silent."""
        await self._validate_conflict_checks(purger.conflict_checks())
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
