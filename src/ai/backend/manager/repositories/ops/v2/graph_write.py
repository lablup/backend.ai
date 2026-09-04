"""The relations of the RBAC graph, bound to a single session.

own: a virtual entity holds an entity, so the entity is listed there and reached
in one hop. govern: a scope rules a virtual entity, so the scope's roles reach
everything it owns. Every entity's own virtual entity owns and governs it. A share
is own under a cap, lent to the scope alone.

Only primitives live here, shared by the entity, share and relation write ops. No
provider hands them out: a repository takes one of those three.
"""

from __future__ import annotations

import uuid
from collections.abc import Collection, Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.id import EntityMembershipID, FieldPath
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.permission import InvalidFieldPermission, VirtualEntityNotFound
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase

type _NodeKey = tuple[EntityType, uuid.UUID]


class V2GraphWriteOpsBase(V2WriteOpsBase):
    """The own and govern primitives every graph-touching write shares."""

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

    async def _own(self, owners: Collection[EntityIdentifier], entity: EntityIdentifier) -> None:
        """Each owner's virtual entity owns the entity, uncapped. A share already there
        becomes own, its cap rows dropped."""
        if not owners:
            return
        node_ids = await self._node_ids([entity, *owners])
        entity_node = node_ids[self._node_key(entity)]
        owner_nodes = [node_ids[self._node_key(owner)] for owner in owners]
        membership_ids = (
            await self._sess.scalars(
                pg_insert(EntityMembershipRow)
                .values([
                    {"virtual_entity_id": owner, "member_entity_id": entity_node, "capped": False}
                    for owner in owner_nodes
                ])
                .on_conflict_do_update(
                    index_elements=["virtual_entity_id", "member_entity_id"],
                    set_={"capped": False},
                )
                .returning(EntityMembershipRow.id)
            )
        ).all()
        await self._sess.execute(
            sa.delete(EntityMembershipCapRow).where(
                EntityMembershipCapRow.membership_id.in_(membership_ids)
            )
        )

    async def _disown(self, owners: Collection[EntityIdentifier], entity: EntityIdentifier) -> None:
        """Each owner's virtual entity stops owning the entity. Silent where it never
        did, or where either side has no virtual entity."""
        if not owners:
            return
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id.in_(self._node_ids_query(list(owners))),
                EntityMembershipRow.member_entity_id == self._node_id_query(entity),
            )
        )

    async def _govern(
        self,
        scopes: Collection[EntityIdentifier],
        entity: EntityIdentifier,
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

    async def _ungovern(
        self, scopes: Collection[EntityIdentifier], entity: EntityIdentifier
    ) -> None:
        """Each scope stops governing the entity's virtual entity. Silent where it
        never did, or where either side has no virtual entity."""
        if not scopes:
            return
        await self._sess.execute(
            sa.delete(ScopeBindingRow).where(
                ScopeBindingRow.virtual_entity_id == self._node_id_query(entity),
                ScopeBindingRow.scope_entity_id.in_(self._node_ids_query(list(scopes))),
            )
        )

    async def _created_in(
        self, scopes: Collection[EntityIdentifier], entity: EntityIdentifier
    ) -> None:
        """Each scope owns and governs the entity — one node lookup for both."""
        if not scopes:
            return
        node_ids = await self._node_ids([entity, *scopes])
        entity_node = node_ids[self._node_key(entity)]
        scope_nodes = [node_ids[self._node_key(scope)] for scope in scopes]
        membership_ids = (
            await self._sess.scalars(
                pg_insert(EntityMembershipRow)
                .values([
                    {"virtual_entity_id": scope, "member_entity_id": entity_node, "capped": False}
                    for scope in scope_nodes
                ])
                .on_conflict_do_update(
                    index_elements=["virtual_entity_id", "member_entity_id"],
                    set_={"capped": False},
                )
                .returning(EntityMembershipRow.id)
            )
        ).all()
        await self._sess.execute(
            sa.delete(EntityMembershipCapRow).where(
                EntityMembershipCapRow.membership_id.in_(membership_ids)
            )
        )
        await self._sess.execute(
            pg_insert(ScopeBindingRow)
            .values([
                {"virtual_entity_id": entity_node, "scope_entity_id": scope, "permission_cap": None}
                for scope in scope_nodes
            ])
            .on_conflict_do_nothing()
        )

    async def _removed_from(
        self, scopes: Collection[EntityIdentifier], entity: EntityIdentifier
    ) -> None:
        """Each scope stops owning and governing the entity — the reverse of
        :meth:`_created_in`. Silent where it never did."""
        await self._disown(scopes, entity)
        await self._ungovern(scopes, entity)

    async def _reset_share(
        self, scope: EntityIdentifier, entity: EntityIdentifier
    ) -> EntityMembershipID:
        """A fresh share of the entity to the scope with nothing lent yet, answered by
        its id. Whatever the scope had of the entity goes first — a share with its cap
        rows, or own — so the share is what holds now. A scope or entity without a
        virtual entity fails."""
        node_ids = await self._node_ids([scope, entity])
        scope_node = node_ids[self._node_key(scope)]
        entity_node = node_ids[self._node_key(entity)]
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                EntityMembershipRow.member_entity_id == entity_node,
            )
        )
        return (
            await self._sess.execute(
                sa.insert(EntityMembershipRow)
                .values({
                    "virtual_entity_id": scope_node,
                    "member_entity_id": entity_node,
                    "capped": True,
                })
                .returning(EntityMembershipRow.id)
            )
        ).scalar_one()

    async def _unshare(self, scope: EntityIdentifier, entities: Sequence[EntityIdentifier]) -> None:
        """The scope's shares of the entities go, cap rows and paths with them. What
        the scope owns is not a share and stays; silent on what was never shared."""
        if not entities:
            return
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id == self._node_id_query(scope),
                EntityMembershipRow.member_entity_id.in_(self._node_ids_query(entities)),
                EntityMembershipRow.capped.is_(True),
            )
        )

    async def _widen_share(
        self,
        scope: EntityIdentifier,
        entity: EntityIdentifier,
        caps: Mapping[Permission, Sequence[FieldPath] | None],
    ) -> None:
        """Add to what the scope already holds of the entity, never taking away: a
        share is opened if there is none, a bit on every field (``None``) raises a bit
        lent on paths, paths join a bit lent on paths and change nothing on a bit lent
        on every field, and what the scope owns stays as it is."""
        if not caps:
            return
        node_ids = await self._node_ids([scope, entity])
        scope_node = node_ids[self._node_key(scope)]
        entity_node = node_ids[self._node_key(entity)]
        # On conflict the row keeps its own `capped` and comes back row-locked, so an
        # own row is left as it is and skipped below; DO NOTHING would return nothing.
        share = (
            await self._sess.execute(
                pg_insert(EntityMembershipRow)
                .values({
                    "virtual_entity_id": scope_node,
                    "member_entity_id": entity_node,
                    "capped": True,
                })
                .on_conflict_do_update(
                    index_elements=["virtual_entity_id", "member_entity_id"],
                    set_={"capped": EntityMembershipRow.__table__.c.capped},
                )
                .returning(EntityMembershipRow.id, EntityMembershipRow.capped)
            )
        ).one()
        if not share.capped:
            return
        whole = [bit for bit, paths in caps.items() if paths is None]
        scoped = {bit: paths for bit, paths in caps.items() if paths is not None}
        cap_stmt = pg_insert(EntityMembershipCapRow).values([
            {"membership_id": share.id, "permission": bit, "all_fields": bit in whole}
            for bit in caps
        ])
        await self._sess.execute(
            cap_stmt.on_conflict_do_update(
                index_elements=["membership_id", "permission"],
                set_={
                    "all_fields": sa.or_(
                        EntityMembershipCapRow.__table__.c.all_fields,
                        cap_stmt.excluded.all_fields,
                    )
                },
            )
        )
        if whole:
            await self._sess.execute(
                sa.delete(EntityMembershipFieldRow).where(
                    EntityMembershipFieldRow.cap_id.in_(
                        sa.select(EntityMembershipCapRow.id).where(
                            EntityMembershipCapRow.membership_id == share.id,
                            EntityMembershipCapRow.permission.in_(whole),
                        )
                    )
                )
            )
        if scoped:
            requested = sa.values(
                sa.column("permission", sa.Integer),
                sa.column("path", sa.String),
                name="requested",
            ).data([(int(bit), path) for bit, paths in scoped.items() for path in paths])
            await self._sess.execute(
                pg_insert(EntityMembershipFieldRow)
                .from_select(
                    ["cap_id", "path"],
                    sa.select(EntityMembershipCapRow.id, requested.c.path)
                    .select_from(requested)
                    .join(
                        EntityMembershipCapRow,
                        EntityMembershipCapRow.permission == requested.c.permission,
                    )
                    .where(
                        EntityMembershipCapRow.membership_id == share.id,
                        EntityMembershipCapRow.all_fields.is_(False),
                    ),
                )
                .on_conflict_do_nothing()
            )

    async def _narrow_share(
        self,
        scope: EntityIdentifier,
        entity: EntityIdentifier,
        caps: Mapping[Permission, Sequence[FieldPath] | None],
    ) -> None:
        """Take back from the scope's share of the entity, never the share itself: a
        bit given as ``None`` goes with its paths, a bit given paths loses them and
        their descendants. A path cannot be taken from a bit lent on every field —
        that raises :class:`InvalidFieldPermission`; take the bit instead. Silent on
        what was never lent, on what the scope owns, and on what was never shared."""
        whole = [bit for bit, paths in caps.items() if paths is None]
        scoped = {bit: paths for bit, paths in caps.items() if paths is not None}
        share_id = sa.select(EntityMembershipRow.id).where(
            EntityMembershipRow.virtual_entity_id == self._node_id_query(scope),
            EntityMembershipRow.member_entity_id == self._node_id_query(entity),
            EntityMembershipRow.capped.is_(True),
        )
        if whole:
            await self._sess.execute(
                sa.delete(EntityMembershipCapRow).where(
                    EntityMembershipCapRow.membership_id.in_(share_id),
                    EntityMembershipCapRow.permission.in_(whole),
                )
            )
        if not scoped:
            return
        on_every_field = (
            await self._sess.scalars(
                sa.select(EntityMembershipCapRow.permission).where(
                    EntityMembershipCapRow.membership_id.in_(share_id),
                    EntityMembershipCapRow.permission.in_(list(scoped)),
                    EntityMembershipCapRow.all_fields.is_(True),
                )
            )
        ).all()
        if on_every_field:
            raise InvalidFieldPermission(
                f"{[Permission(bit) for bit in on_every_field]!r} lent on every field; a path"
                " cannot narrow it."
            )
        scoped_cap_ids = sa.select(EntityMembershipCapRow.id).where(
            EntityMembershipCapRow.membership_id.in_(share_id),
            EntityMembershipCapRow.permission.in_(list(scoped)),
        )
        await self._sess.execute(
            sa.delete(EntityMembershipFieldRow).where(
                EntityMembershipFieldRow.cap_id.in_(scoped_cap_ids),
                sa.or_(*[
                    sa.and_(
                        EntityMembershipFieldRow.cap_id.in_(
                            sa.select(EntityMembershipCapRow.id).where(
                                EntityMembershipCapRow.membership_id.in_(share_id),
                                EntityMembershipCapRow.permission == bit,
                            )
                        ),
                        sa.or_(*[
                            sa.or_(
                                EntityMembershipFieldRow.path == path,
                                EntityMembershipFieldRow.path.like(f"{path}.%"),
                            )
                            for path in paths
                        ]),
                    )
                    for bit, paths in scoped.items()
                ]),
            )
        )

    async def _insert_caps(
        self,
        membership_id: EntityMembershipID,
        caps: Mapping[Permission, Sequence[FieldPath] | None],
    ) -> None:
        """One cap row per bit — on every field for ``None``, on the listed paths
        otherwise — in one statement each."""
        if not caps:
            return
        cap_ids = (
            await self._sess.execute(
                sa.insert(EntityMembershipCapRow)
                .values([
                    {"membership_id": membership_id, "permission": bit, "all_fields": paths is None}
                    for bit, paths in caps.items()
                ])
                .returning(EntityMembershipCapRow.id, EntityMembershipCapRow.permission)
            )
        ).all()
        by_bit = {Permission(row.permission): row.id for row in cap_ids}
        path_rows = [
            {"cap_id": by_bit[bit], "path": path}
            for bit, paths in caps.items()
            if paths is not None
            for path in paths
        ]
        if path_rows:
            await self._sess.execute(
                pg_insert(EntityMembershipFieldRow).values(path_rows).on_conflict_do_nothing()
            )

    def _node_key(self, entity: EntityIdentifier) -> _NodeKey:
        return (entity.entity_type(), entity)

    def _node_id_query(self, entity: EntityIdentifier) -> sa.ScalarSelect[Any]:
        """The entity's virtual entity id as a scalar subquery; NULL without one, so a
        comparison on it matches nothing."""
        return (
            sa.select(VirtualEntityRow.id)
            .where(
                VirtualEntityRow.entity_type == entity.entity_type(),
                VirtualEntityRow.entity_id == entity,
            )
            .scalar_subquery()
        )

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
