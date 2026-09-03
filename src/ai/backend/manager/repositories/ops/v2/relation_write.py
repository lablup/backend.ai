"""Relation writes of the v2 ops: a row linking two entities, and the read each
side gets on the other.

A relation (a project and a resource group) puts neither entity under the other. What
it does in the graph is two READ-capped shares, one per direction, so the roles in
each entity's scope see the other entity and nothing it owns. The relation row itself is the domain's
table; its shape and conflict handling come from the spec (BEP-1075).
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
        self, creator: RelationCreator[TRow], left: EntityIdentifier, right: EntityIdentifier
    ) -> None:
        """Link the two entities: the relation row, then READ on each from the other's
        scope. A pair already linked is handled as the spec's conflict values say;
        the grants are restated either way, so a narrowed cap is restored."""
        row = creator.build_row(left, right)
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
        await self.grant_entities(self._mutual_read(left, right))

    async def purge_relation[TRow: Base](
        self, purger: RelationPurger[TRow], left: EntityIdentifier, right: EntityIdentifier
    ) -> None:
        """Unlink the two entities: the relation row and both READ grants go. Silent
        when the pair was never linked."""
        await self._validate_conflict_checks(purger.conflict_checks())
        stmt = sa.delete(purger.row_class())
        for condition in purger.conditions(left, right):
            stmt = stmt.where(condition())
        await self._sess.execute(stmt)
        await self.revoke_entities([right], grantee=left)
        await self.revoke_entities([left], grantee=right)

    def _mutual_read(self, left: EntityIdentifier, right: EntityIdentifier) -> list[EntityGrant]:
        return [
            EntityGrant(entity=right, grantee=left, permission_cap=Permission.READ),
            EntityGrant(entity=left, grantee=right, permission_cap=Permission.READ),
        ]
