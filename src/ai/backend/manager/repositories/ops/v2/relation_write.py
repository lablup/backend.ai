"""Relation writes of the v2 ops: a row linking a scope to a target, and what each
side gets to read of the other.

A relation (a project and a resource group) is asymmetric in the graph. The scope
governs the target under a READ cap, so the scope's roles read the target and what
it owns (a resource group's agents, a registry's images). The target is only shared
the scope, under a READ cap, so the target's roles read the scope itself and nothing
the scope owns. The relation row is the domain's table; its shape and conflict
handling come from the spec (BEP-1075).
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.membership import EntityGrant
from ai.backend.manager.models.specs.relation import RelationCreator, RelationPurger
from ai.backend.manager.repositories.ops.v2.grant_write import V2GrantWriteOps


class V2RelationWriteOps(V2GrantWriteOps):
    """Relations between existing entities, bound to a single session."""

    async def create_relation[TRow: Base](
        self, creator: RelationCreator[TRow], scope: EntityIdentifier, target: EntityIdentifier
    ) -> None:
        """Link the scope to the target: the relation row, the scope governing the
        target under READ, and the scope shared to the target under READ. A pair
        already linked is handled as the spec's conflict values say; the share is
        restated either way, so a narrowed cap is restored."""
        row = creator.build_row(scope, target)
        mapper = sa.inspect(type(row))
        column_keys = {c.key for c in mapper.columns}
        stmt = pg_insert(type(row)).values({
            k: v for k, v in row.__dict__.items() if k in column_keys
        })
        conflict_values = creator.build_conflict_values()
        if conflict_values is None:
            stmt = stmt.on_conflict_do_nothing(index_elements=creator.index_elements())
        else:
            stmt = stmt.on_conflict_do_update(
                index_elements=creator.index_elements(), set_=conflict_values
            )
        try:
            await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(
                self._parse_integrity_error(e), creator.integrity_error_checks()
            )
        await self._govern([scope], target, cap=Permission.READ)
        await self.grant_entities([
            EntityGrant(entity=scope, grantee=target, permission_cap=Permission.READ)
        ])

    async def purge_relation[TRow: Base](
        self, purger: RelationPurger[TRow], scope: EntityIdentifier, target: EntityIdentifier
    ) -> None:
        """Unlink the scope from the target: the relation row, the govern and the
        share go. Silent when the pair was never linked."""
        await self._validate_conflict_checks(purger.conflict_checks())
        stmt = sa.delete(purger.row_class())
        for condition in purger.conditions(scope, target):
            stmt = stmt.where(condition())
        await self._sess.execute(stmt)
        await self._ungovern([scope], target)
        await self.revoke_entities([scope], grantee=target)
