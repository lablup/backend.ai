"""Permission reads: what a role holds per (scope, entity_type) key, field scopes
included, composed from the per-bit rows and their path rows; and what a user
effectively holds on an entity, resolved through the graph."""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityID, EntityIdentifier, EntityType
from ai.backend.common.data.permission.id import FieldPath
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.virtual_entity import (
    GovernCheckKey,
    OwnCheckKey,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_field import PermissionFieldRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.specs.permission import PermissionEntry, PermissionKey
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps


@dataclass(frozen=True)
class _GroupKey:
    """Keys resolved in one round-trip: ``entity_type`` matches the graph rows,
    ``subject_entity_type`` the permission rows."""

    user_id: uuid.UUID
    entity_type: EntityType
    subject_entity_type: EntityType


class PermissionReadOps(V2ReadOps):
    """The general v2 read ops plus the role permission read."""

    async def permissions(
        self, role_id: RoleID, keys: Sequence[PermissionKey]
    ) -> dict[PermissionKey, PermissionEntry]:
        """The named keys' entries; a key holding nothing is absent."""
        if not keys:
            return {}
        by_columns = {
            (str(k.scope.entity_type()), str(k.scope), str(k.entity_type)): k for k in keys
        }
        rows = (
            await self._sess.execute(
                sa.select(
                    PermissionRow.scope_type,
                    PermissionRow.scope_id,
                    PermissionRow.entity_type,
                    PermissionRow.permission,
                    PermissionRow.all_fields,
                    PermissionFieldRow.path,
                )
                .select_from(PermissionRow)
                .outerjoin(PermissionFieldRow, PermissionFieldRow.permission_id == PermissionRow.id)
                .where(
                    PermissionRow.role_id == role_id,
                    self._key_filter(keys),
                )
            )
        ).all()
        whole: dict[PermissionKey, Permission] = {}
        fields: dict[PermissionKey, dict[FieldPath, Permission]] = {}
        for row in rows:
            key = by_columns[(str(row.scope_type), row.scope_id, str(row.entity_type))]
            whole.setdefault(key, Permission.NONE)
            if row.all_fields:
                whole[key] |= row.permission
            elif row.path is not None:
                scoped = fields.setdefault(key, {})
                scoped[row.path] = scoped.get(row.path, Permission.NONE) | row.permission
        return {
            key: PermissionEntry(
                scope=key.scope,
                entity_type=key.entity_type,
                permission=whole[key],
                fields=fields.get(key, {}),
            )
            for key in whole
        }

    def _key_filter(self, keys: Sequence[PermissionKey]) -> sa.ColumnElement[bool]:
        return sa.tuple_(
            PermissionRow.scope_type, PermissionRow.scope_id, PermissionRow.entity_type
        ).in_([self._key_columns(k.scope, k.entity_type) for k in keys])

    def _key_columns(
        self, scope: EntityIdentifier, entity_type: EntityType
    ) -> tuple[EntityType, str, EntityType]:
        return (scope.entity_type(), str(scope), entity_type)

    # -- effective permissions over the graph ------------------------------------------

    async def owned_permissions(
        self,
        keys: Collection[OwnCheckKey],
    ) -> Mapping[OwnCheckKey, Permission]:
        """The bits each user holds on each entity through own and govern.

        Every path ``entity <- own - ve <- govern - scope <- role`` contributes the
        role's permission clipped by the govern cap and the share cap on the path;
        the paths OR together. Own is not capped; a share answers only for the shared
        entity's own type and only through the ve's own govern. Every-field rows only:
        path-scoped bits wait for the field check. Keys sharing ``(user, entity type)``
        share one round-trip; a key nothing reaches maps to :attr:`Permission.NONE`.
        """
        if not keys:
            return {}
        groups: defaultdict[_GroupKey, list[OwnCheckKey]] = defaultdict(list)
        for key in keys:
            groups[
                _GroupKey(
                    user_id=key.user_id,
                    entity_type=key.entity.entity_type(),
                    subject_entity_type=key.entity.entity_type(),
                )
            ].append(key)

        result: dict[OwnCheckKey, Permission] = {}
        for group_key, members in groups.items():
            granted = await self._resolve_group(group_key, [k.entity for k in members])
            for key in members:
                result[key] = granted.get(key.entity, Permission.NONE)
        return result

    async def governed_permissions(
        self,
        keys: Collection[GovernCheckKey],
    ) -> Mapping[GovernCheckKey, Permission]:
        """The bits each user holds on ``entity_type`` within each scope through the
        scopes governing it."""
        if not keys:
            return {}
        groups: defaultdict[_GroupKey, list[GovernCheckKey]] = defaultdict(list)
        for key in keys:
            groups[
                _GroupKey(
                    user_id=key.user_id,
                    entity_type=EntityType(key.scope.scope_type),
                    subject_entity_type=key.entity_type,
                )
            ].append(key)

        result: dict[GovernCheckKey, Permission] = {}
        for group_key, members in groups.items():
            granted = await self._resolve_group(group_key, [k.scope.scope_id for k in members])
            for key in members:
                result[key] = granted.get(key.scope.scope_id, Permission.NONE)
        return result

    async def _resolve_group(
        self, group_key: _GroupKey, entity_ids: Sequence[EntityID]
    ) -> Mapping[EntityID, Permission]:
        result = await self._sess.execute(self._owned_query(group_key, entity_ids))
        return {row.entity_id: Permission(row.granted) for row in result}

    def _owned_query(
        self, group_key: _GroupKey, entity_ids: Sequence[EntityID]
    ) -> sa.Select[tuple[EntityID, int]]:
        """Run the virtual-entity-chain query for a single ``(user_id, entity_type,
        subject_entity_type)`` group with N entity_ids.

        Returns a mapping from entity_id to its effective (cap-clipped, OR-combined)
        :class:`Permission`. Entities with no reachable grant are absent from the map.
        """
        own = EntityMembershipRow.__table__
        share_cap = EntityMembershipCapRow.__table__
        govern = ScopeBindingRow.__table__
        entity = VirtualEntityRow.__table__.alias("entity")
        governor = VirtualEntityRow.__table__.alias("governor")
        perm = PermissionRow.__table__
        roles = RoleRow.__table__
        user_roles = UserRoleRow.__table__

        full_cap = int(Permission.full())
        # entity <- own - ve <- govern - governor <- permission <- role <- user; one row
        # per entity, the paths OR-ed in SQL after each is clipped by its govern cap.
        return (
            sa.select(
                entity.c.entity_id,
                sa.func.bit_or(
                    perm.c.permission.op("&")(sa.func.coalesce(govern.c.permission_cap, full_cap))
                ).label("granted"),
            )
            .select_from(
                own.join(entity, entity.c.id == own.c.member_entity_id)
                .join(govern, govern.c.virtual_entity_id == own.c.virtual_entity_id)
                .join(governor, governor.c.id == govern.c.scope_entity_id)
                .join(
                    perm,
                    sa.and_(
                        perm.c.scope_type == governor.c.entity_type,
                        # virtual_entities.entity_id is a native UUID; permissions.scope_id
                        # stores its canonical string form. Cast to compare.
                        perm.c.scope_id == sa.cast(governor.c.entity_id, sa.String),
                        perm.c.entity_type == group_key.subject_entity_type,
                        perm.c.all_fields.is_(True),
                    ),
                )
                .join(roles, roles.c.id == perm.c.role_id)
                .join(user_roles, user_roles.c.role_id == roles.c.id)
                .outerjoin(
                    share_cap,
                    sa.and_(
                        share_cap.c.membership_id == own.c.id,
                        share_cap.c.permission == perm.c.permission,
                        share_cap.c.all_fields.is_(True),
                    ),
                )
            )
            .where(
                entity.c.entity_type == group_key.entity_type,
                entity.c.entity_id.in_(entity_ids),
                user_roles.c.user_id == group_key.user_id,
                roles.c.status == RoleStatus.ACTIVE,
                # Own answers through every governor. A share answers only with a cap
                # row on every field for the bit, only for the shared entity's own type,
                # and only through the ve's own govern. Path-capped bits wait for the
                # field check.
                sa.or_(
                    own.c.capped.is_(False),
                    sa.and_(
                        share_cap.c.id.is_not(None),
                        entity.c.entity_type == group_key.subject_entity_type,
                        govern.c.scope_entity_id == govern.c.virtual_entity_id,
                    ),
                ),
            )
            .group_by(entity.c.entity_id)
        )
