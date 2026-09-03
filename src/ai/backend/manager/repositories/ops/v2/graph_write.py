"""The two relations of the RBAC graph, bound to a single session.

own: a virtual entity holds an entity, so the entity is listed there and reached
in one hop. govern: a scope rules a virtual entity, so the scope's roles reach
everything it owns. Every entity's own virtual entity owns and governs it. A cap on
govern bounds what the scope reaches through it; a relation is the one writer of
such a cap.
"""

from __future__ import annotations

import uuid
from collections.abc import Collection, Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.permission import VirtualEntityNotFound
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase

type _NodeKey = tuple[EntityType, uuid.UUID]


class V2GraphWriteOps(V2WriteOpsBase):
    """The own and govern writes every graph-touching concern shares."""

    async def _provision(self, entities: Sequence[EntityIdentifier]) -> None:
        """Put each entity into the graph: its virtual entity, which owns and governs
        it. The reverse of :meth:`_teardown`. Idempotent: an existing node is a no-op."""
        if not entities:
            return
        inserted = (
            await self._sess.execute(
                pg_insert(VirtualEntityRow)
                .values([{"entity_type": e.entity_type(), "entity_id": e} for e in entities])
                .on_conflict_do_nothing(index_elements=["entity_type", "entity_id"])
                .returning(VirtualEntityRow.id)
            )
        ).all()
        if not inserted:
            return
        await self._sess.execute(
            pg_insert(EntityMembershipRow)
            .values([
                {"virtual_entity_id": row.id, "member_entity_id": row.id, "capped": False}
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(
            pg_insert(ScopeBindingRow)
            .values([
                {"virtual_entity_id": row.id, "scope_entity_id": row.id, "permission_cap": None}
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )

    async def _teardown(self, entity: EntityIdentifier) -> None:
        """Remove what the entity left: permissions granted on it, its virtual entity
        (every relation naming it goes with it by FK), and the labels put on it."""
        await self._sess.execute(
            sa.delete(PermissionRow).where(PermissionRow.scope_id == str(entity))
        )
        await self._sess.execute(
            sa.delete(VirtualEntityRow).where(
                VirtualEntityRow.entity_type == entity.entity_type(),
                VirtualEntityRow.entity_id == entity,
            )
        )
        await self._sess.execute(
            sa.delete(EntityLabelRow).where(
                EntityLabelRow.entity_type == entity.entity_type(),
                EntityLabelRow.entity_id == entity,
            )
        )

    async def _own(self, entity: EntityIdentifier, owners: Collection[EntityIdentifier]) -> None:
        """Each owner's virtual entity owns the entity, uncapped. Idempotent."""
        if not owners:
            return
        node_ids = await self._node_ids([entity, *owners])
        entity_node = node_ids[self._node_key(entity)]
        await self._sess.execute(
            pg_insert(EntityMembershipRow)
            .values([
                {
                    "virtual_entity_id": node_ids[self._node_key(owner)],
                    "member_entity_id": entity_node,
                    "capped": False,
                }
                for owner in owners
            ])
            .on_conflict_do_nothing()
        )

    async def _govern(
        self,
        entity: EntityIdentifier,
        scopes: Collection[EntityIdentifier],
        cap: Permission | None = None,
    ) -> None:
        """Each scope governs the entity's virtual entity, bounded by ``cap`` (``None``
        = no bound). Idempotent: a scope already governing keeps its cap."""
        if not scopes:
            return
        node_ids = await self._node_ids([entity, *scopes])
        entity_node = node_ids[self._node_key(entity)]
        await self._sess.execute(
            pg_insert(ScopeBindingRow)
            .values([
                {
                    "virtual_entity_id": entity_node,
                    "scope_entity_id": node_ids[self._node_key(scope)],
                    "permission_cap": cap,
                }
                for scope in scopes
            ])
            .on_conflict_do_nothing()
        )

    async def _created_in(
        self, entity: EntityIdentifier, scopes: Collection[EntityIdentifier]
    ) -> None:
        """Each scope owns and governs the entity — one node lookup for both."""
        if not scopes:
            return
        node_ids = await self._node_ids([entity, *scopes])
        entity_node = node_ids[self._node_key(entity)]
        scope_nodes = [node_ids[self._node_key(scope)] for scope in scopes]
        await self._sess.execute(
            pg_insert(EntityMembershipRow)
            .values([
                {"virtual_entity_id": scope, "member_entity_id": entity_node, "capped": False}
                for scope in scope_nodes
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(
            pg_insert(ScopeBindingRow)
            .values([
                {"virtual_entity_id": entity_node, "scope_entity_id": scope, "permission_cap": None}
                for scope in scope_nodes
            ])
            .on_conflict_do_nothing()
        )

    async def _disown(self, entity: EntityIdentifier, owners: Collection[EntityIdentifier]) -> None:
        """Each owner's virtual entity stops owning the entity. Silent where it never
        did, or where either side has no virtual entity."""
        if not owners:
            return
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id.in_(self._node_ids_query(list(owners))),
                EntityMembershipRow.member_entity_id.in_(self._node_ids_query([entity])),
            )
        )

    async def _ungovern(
        self, entity: EntityIdentifier, scopes: Collection[EntityIdentifier]
    ) -> None:
        """Each scope stops governing the entity's virtual entity. Silent where it
        never did, or where either side has no virtual entity."""
        if not scopes:
            return
        await self._sess.execute(
            sa.delete(ScopeBindingRow).where(
                ScopeBindingRow.virtual_entity_id.in_(self._node_ids_query([entity])),
                ScopeBindingRow.scope_entity_id.in_(self._node_ids_query(list(scopes))),
            )
        )

    def _node_key(self, entity: EntityIdentifier) -> _NodeKey:
        return (entity.entity_type(), entity)

    def _node_ids_query(
        self, entities: Sequence[EntityIdentifier]
    ) -> sa.Select[tuple[VirtualEntityID]]:
        """The entities' virtual entity ids; an entity without one contributes
        nothing, so a delete keyed on it matches nothing."""
        return sa.select(VirtualEntityRow.id).where(
            sa.tuple_(VirtualEntityRow.entity_type, VirtualEntityRow.entity_id).in_([
                self._node_key(e) for e in entities
            ])
        )

    async def _node_ids(
        self, entities: Sequence[EntityIdentifier]
    ) -> dict[_NodeKey, VirtualEntityID]:
        """Resolve-or-fail, never get-or-create: an entity without a virtual entity
        raises :class:`VirtualEntityNotFound` naming every missing one."""
        rows = (
            await self._sess.execute(
                sa.select(
                    VirtualEntityRow.entity_type, VirtualEntityRow.entity_id, VirtualEntityRow.id
                ).where(
                    sa.tuple_(VirtualEntityRow.entity_type, VirtualEntityRow.entity_id).in_([
                        self._node_key(e) for e in entities
                    ])
                )
            )
        ).all()
        resolved = {(row.entity_type, row.entity_id): row.id for row in rows}
        missing = [e for e in entities if self._node_key(e) not in resolved]
        if missing:
            raise VirtualEntityNotFound(
                "No virtual entity for entities: "
                + ", ".join(f"{e.entity_type()}:{e}" for e in missing)
            )
        return resolved
