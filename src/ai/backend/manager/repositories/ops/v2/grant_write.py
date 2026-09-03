"""Grant writes of the v2 ops: access to an existing entity, offered, handed out and
taken back.

A grant records the entity as a member of the grantee's virtual entity with a cap,
which is what ``PermissionControllerDBSource._resolve_permissions_for_virtual_entity_group``
clips the grantee's permissions to. Creation-time belonging is not this: see
``models/specs/AGENTS.md``.

A belonging edge is not capped and clips nothing. A share is capped: each
``entity_membership_caps`` row lets one operation bit through, on every field with
``all_fields`` or on its ``entity_membership_fields`` paths and their descendants
without. A share with no cap rows lets nothing through — enrollment without
access — and goes only by an explicit revoke of the edge.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.id import (
    EntityMembershipCapID,
    EntityMembershipID,
    FieldPath,
)
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.errors.permission import InvalidFieldPermission
from ai.backend.manager.models.entity_invitation.updaters import EntityInvitationAcceptUpdater
from ai.backend.manager.models.specs.membership import EntityGrant, EntityMembershipEntry
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase

_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$")

type _EdgeKey = tuple[VirtualEntityID, VirtualEntityID]


@dataclass(frozen=True)
class _CapRow:
    """One cap row of an edge, with the paths it is scoped to."""

    id: EntityMembershipCapID
    all_fields: bool
    paths: frozenset[FieldPath]


@dataclass(frozen=True)
class _Edge:
    """One membership edge and its cap rows per bit."""

    capped: bool
    caps: Mapping[Permission, _CapRow]


class V2GrantWriteOps(V2WriteOpsBase):
    """Grants over existing entities, bound to a single session."""

    async def grant_entities(self, grants: Sequence[EntityGrant]) -> None:
        """Hand each entity to its grantee, bounded by the grant's cap.

        Re-granting rewrites the cap rows and their paths rather than keeping the
        earlier ones: a grant states the ceiling that holds now, so a widened or
        narrowed one has to win. A grantee with no virtual entity fails, as every
        membership write does; the entity's node is provisioned if it is missing,
        since entities created before the virtual-entity rollout have none.
        """
        if not grants:
            return
        for grant in grants:
            self._validate_grant(grant)
        keys = await self._edge_keys([(g.grantee, g.entity) for g in grants])
        ids = await self._upsert_edges(keys, capped=True)
        await self._sess.execute(
            sa.delete(EntityMembershipCapRow).where(
                EntityMembershipCapRow.membership_id.in_(list(ids.values()))
            )
        )
        for key, grant in zip(keys, grants, strict=True):
            for bit in self._bits_of(grant.permission_cap):
                await self._insert_cap(ids[key], bit, True, ())
            for bit, paths in self._scoped_paths(grant.fields).items():
                await self._insert_cap(ids[key], bit, False, paths)

    async def enroll_entities(self, entries: Sequence[EntityMembershipEntry]) -> None:
        """Make each entity belong to its parent after creation — an ownership move.

        Belonging is not capped: a share edge already there is turned into
        belonging, its cap rows dropped.
        """
        if not entries:
            return
        keys = await self._edge_keys([(e.parent, e.member) for e in entries])
        ids = await self._upsert_edges(keys, capped=False)
        await self._sess.execute(
            sa.delete(EntityMembershipCapRow).where(
                EntityMembershipCapRow.membership_id.in_(list(ids.values()))
            )
        )

    async def widen_entity_grants(self, grants: Sequence[EntityGrant]) -> None:
        """Add each grant's cap to what the grantee already holds, never taking away.

        Where :meth:`grant_entities` states the ceiling that holds now, this only ever
        raises it: bits join, a belonging edge (no ceiling) stays as it is, paths join
        a bit already scoped to paths, and a bit reaching every field drops the paths
        it makes redundant.
        """
        if not grants:
            return
        for grant in grants:
            self._validate_grant(grant)
        keys = await self._edge_keys([(g.grantee, g.entity) for g in grants])
        ids = await self._upsert_edges(keys, capped=None)
        current = await self._locked_edges(list(ids.values()))
        for key, grant in zip(keys, grants, strict=True):
            membership_id = ids[key]
            edge = current[membership_id]
            if not edge.capped:
                continue
            for bit in self._bits_of(grant.permission_cap):
                cap = edge.caps.get(bit)
                if cap is None:
                    await self._insert_cap(membership_id, bit, True, ())
                elif not cap.all_fields:
                    await self._sess.execute(
                        sa.update(EntityMembershipCapRow)
                        .values(all_fields=True)
                        .where(EntityMembershipCapRow.id == cap.id)
                    )
                    await self._sess.execute(
                        sa.delete(EntityMembershipFieldRow).where(
                            EntityMembershipFieldRow.cap_id == cap.id
                        )
                    )
            for bit, paths in self._scoped_paths(grant.fields).items():
                cap = edge.caps.get(bit)
                if cap is None:
                    await self._insert_cap(membership_id, bit, False, paths)
                elif not cap.all_fields:
                    await self._insert_cap_paths(cap.id, paths)

    async def revoke_entities(
        self, entities: Sequence[EntityIdentifier], grantee: EntityIdentifier
    ) -> None:
        """Take the entities back from the grantee's scope, cap rows and paths with
        them.

        Silent on what was never granted — a revoke states the absence it leaves, not
        that it found something to remove.
        """
        if not entities:
            return
        scope_ids = await self._resolve_virtual_entity_ids([grantee])
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id
                == scope_ids[(grantee.entity_type(), grantee)],
                EntityMembershipRow.member_entity_id.in_(self._virtual_entity_ids_query(entities)),
            )
        )

    async def accept_entity_invitation(
        self, updater: EntityInvitationAcceptUpdater
    ) -> EntityInvitationData | None:
        """Settle the invitation as accepted and hand its entity to the invitee.

        ``None`` when nothing was settled — the invitation is gone, already answered,
        or addressed to somebody else; the guards do not say which. Turning one down
        grants nothing and goes through the plain guarded update instead, which is why
        only this direction is a primitive: the settle and the grant cannot come apart.

        The grant widens rather than states: an offer is somebody else's, and accepting
        one must not cost the invitee access they already had. Setting a cap exactly is
        :meth:`grant_entities`, which an invitation never reaches. An invitation
        without a cap hands over every operation on every field.
        """
        row = await self._update_guarded_row_returning(
            updater.row_class,
            updater.target_id_column(),
            updater.target_id_value(),
            updater.guard_conditions(),
            updater.build_values(),
            updater.integrity_error_checks,
        )
        if row is None:
            return None
        data = updater.to_data(row)
        await self.widen_entity_grants([
            EntityGrant(
                entity=data.target,
                grantee=updater.invitee_user_id,
                permission_cap=(
                    data.permission_cap if data.permission_cap is not None else Permission.full()
                ),
            )
        ])
        return data

    # -- Edges -------------------------------------------------------------------------

    async def _edge_keys(
        self, pairs: Sequence[tuple[EntityIdentifier, EntityIdentifier]]
    ) -> list[_EdgeKey]:
        """(parent node, member node) per pair, provisioning the members' missing
        nodes; a parent without a node fails."""
        await self._provision_entities([member for _, member in pairs])
        node_ids = await self._resolve_virtual_entity_ids([
            *(parent for parent, _ in pairs),
            *(member for _, member in pairs),
        ])
        return [
            (
                node_ids[(parent.entity_type(), parent)],
                node_ids[(member.entity_type(), member)],
            )
            for parent, member in pairs
        ]

    async def _upsert_edges(
        self, keys: Sequence[_EdgeKey], *, capped: bool | None
    ) -> dict[_EdgeKey, EntityMembershipID]:
        """Insert the edges and answer their ids; ``capped`` states the edges
        (``None`` inserts a capped edge where none exists and leaves an existing one
        as it is)."""
        stmt = pg_insert(EntityMembershipRow).values([
            {
                "virtual_entity_id": key[0],
                "member_entity_id": key[1],
                "capped": capped or capped is None,
            }
            for key in keys
        ])
        if capped is None:
            await self._sess.execute(
                stmt.on_conflict_do_nothing(
                    index_elements=["virtual_entity_id", "member_entity_id"]
                )
            )
        else:
            await self._sess.execute(
                stmt.on_conflict_do_update(
                    index_elements=["virtual_entity_id", "member_entity_id"],
                    set_={"capped": capped},
                )
            )
        rows = (
            await self._sess.execute(
                sa.select(
                    EntityMembershipRow.id,
                    EntityMembershipRow.virtual_entity_id,
                    EntityMembershipRow.member_entity_id,
                ).where(
                    sa.tuple_(
                        EntityMembershipRow.virtual_entity_id,
                        EntityMembershipRow.member_entity_id,
                    ).in_(list(keys))
                )
            )
        ).all()
        return {(row.virtual_entity_id, row.member_entity_id): row.id for row in rows}

    async def _locked_edges(
        self, ids: Sequence[EntityMembershipID]
    ) -> dict[EntityMembershipID, _Edge]:
        rows = (
            await self._sess.execute(
                sa.select(EntityMembershipRow.id, EntityMembershipRow.capped)
                .where(EntityMembershipRow.id.in_(list(ids)))
                .with_for_update()
            )
        ).all()
        caps: dict[EntityMembershipID, dict[Permission, _CapRow]] = {row.id: {} for row in rows}
        cap_rows = (
            await self._sess.execute(
                sa.select(
                    EntityMembershipCapRow.id,
                    EntityMembershipCapRow.membership_id,
                    EntityMembershipCapRow.permission,
                    EntityMembershipCapRow.all_fields,
                    EntityMembershipFieldRow.path,
                )
                .select_from(EntityMembershipCapRow)
                .outerjoin(
                    EntityMembershipFieldRow,
                    EntityMembershipFieldRow.cap_id == EntityMembershipCapRow.id,
                )
                .where(EntityMembershipCapRow.membership_id.in_(list(ids)))
            )
        ).all()
        paths: dict[EntityMembershipCapID, set[FieldPath]] = {}
        heads: dict[EntityMembershipCapID, tuple[EntityMembershipID, Permission, bool]] = {}
        for cap_row in cap_rows:
            heads[cap_row.id] = (
                cap_row.membership_id,
                Permission(cap_row.permission),
                cap_row.all_fields,
            )
            if cap_row.path is not None:
                paths.setdefault(cap_row.id, set()).add(cap_row.path)
        for cap_id, (membership_id, bit, all_fields) in heads.items():
            caps[membership_id][bit] = _CapRow(
                id=cap_id, all_fields=all_fields, paths=frozenset(paths.get(cap_id, ()))
            )
        return {row.id: _Edge(capped=row.capped, caps=caps[row.id]) for row in rows}

    async def _insert_cap(
        self,
        membership_id: EntityMembershipID,
        bit: Permission,
        all_fields: bool,
        paths: Iterable[FieldPath],
    ) -> None:
        row = EntityMembershipCapRow(
            membership_id=membership_id, permission=bit, all_fields=all_fields
        )
        self._sess.add(row)
        await self._sess.flush()
        await self._insert_cap_paths(row.id, paths)

    async def _insert_cap_paths(
        self, cap_id: EntityMembershipCapID, paths: Iterable[FieldPath]
    ) -> None:
        values = [{"cap_id": cap_id, "path": path} for path in paths]
        if not values:
            return
        await self._sess.execute(
            pg_insert(EntityMembershipFieldRow).values(values).on_conflict_do_nothing()
        )

    # -- Values ------------------------------------------------------------------------

    def _validate_grant(self, grant: EntityGrant) -> None:
        for path, bits in grant.fields.items():
            if not _PATH_PATTERN.match(path):
                raise InvalidFieldPermission(f"Malformed field path {path!r}.")
            if bits & ~Permission.field_bearing() or not bits:
                raise InvalidFieldPermission(
                    f"Field {path!r} carries {bits!r}; a field scope holds READ|UPDATE bits only."
                )
            if bits & grant.permission_cap:
                raise InvalidFieldPermission(
                    f"Field {path!r} states {bits & grant.permission_cap!r}, which the cap"
                    " already holds on every field."
                )
