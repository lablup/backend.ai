"""Role preset writes: keep the roles a preset instantiated in step with the preset.

A role records the preset it came from (``roles.role_preset_id``). When the preset
changes, every such role is brought back to what the preset now declares; a role with
no recorded preset is never touched.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import ClassVar

import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.scope_source import ScopeSource
from ai.backend.manager.models.specs.permission import PermissionEntry
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.ops.v2.permission.write import PermissionWriteOps

# Derived roles re-synced per round trip; a preset may have one role per scope.
_SYNC_CHUNK_SIZE = 200


class RolePresetWriteOps(PermissionWriteOps):
    """The permission write ops plus the sync of a preset's derived roles."""

    _scope_rows: ClassVar[Mapping[EntityType, type[ScopeSource]]] = {
        ContainerRegistryEntityType(): ContainerRegistryRow,
        DomainEntityType(): DomainRow,
        ProjectEntityType(): ProjectRow,
        ResourceGroupEntityType(): ResourceGroupRow,
        UserEntityType(): UserRow,
    }

    async def sync_preset_roles(self, preset_id: RolePresetID) -> None:
        """Bring every role instantiated from the preset to what it now declares: the
        name its rule yields, its ``auto_assign``, and exactly its permissions on the
        role's own scope. Grants already made are not revisited.

        A role sits in the scope that provisioned it, so a role whose scope is not of
        the preset's scope type is simply not among the roles found here.
        """
        preset = await self._sess.get(RolePresetRow, preset_id)
        if preset is None:
            return
        scope_type = EntityType(EntityType(preset.scope_type.to_element().value))
        granted = await self._preset_grants(preset_id)
        roles = await self._derived_roles(preset_id, scope_type)
        for start in range(0, len(roles), _SYNC_CHUNK_SIZE):
            await self._sync_roles(
                preset, scope_type, granted, dict(roles[start : start + _SYNC_CHUNK_SIZE])
            )

    async def _sync_roles(
        self,
        preset: RolePresetRow,
        scope_type: EntityType,
        granted: Mapping[EntityType, Permission],
        entities: Mapping[RoleID, EntityIdentifier],
    ) -> None:
        held = await self._held_entity_types(list(entities))
        for role_id, entity in entities.items():
            entries = [
                PermissionEntry(
                    entity_type=entity_type,
                    permission=granted.get(entity_type, Permission.NONE),
                )
                for entity_type in granted.keys() | held.get(role_id, set())
            ]
            await self.set_permissions(role_id, entries)
        await self._sess.execute(
            sa.update(RoleRow)
            .where(RoleRow.id.in_(list(entities)))
            .values(auto_assign=preset.auto_assign)
        )
        names = await self._rendered_names(preset, scope_type, entities)
        if names:
            roles = RoleRow.__table__
            await self._sess.execute(
                sa.update(roles)
                .where(roles.c.id == sa.bindparam("b_role_id"))
                .values(name=sa.bindparam("b_name")),
                [{"b_role_id": role_id, "b_name": name} for role_id, name in names.items()],
            )

    async def _preset_grants(self, preset_id: RolePresetID) -> dict[EntityType, Permission]:
        """The permission mask the preset declares per entity type."""
        rows = await self._sess.scalars(
            sa.select(RolePermissionPresetRow).where(
                RolePermissionPresetRow.role_preset_id == preset_id
            )
        )
        granted: dict[EntityType, Permission] = {}
        for row in rows:
            permission = Permission.from_operation(row.operation)
            if permission == Permission.NONE:
                continue
            entity_type = EntityType(row.entity_type.to_element().value)
            granted[entity_type] = granted.get(entity_type, Permission.NONE) | permission
        return granted

    async def _derived_roles(
        self, preset_id: RolePresetID, scope_type: EntityType
    ) -> list[tuple[RoleID, EntityIdentifier]]:
        """Each role the preset instantiated with the scope of ``scope_type`` it sits in."""
        rows = (
            await self._sess.execute(
                sa.select(RoleRow.id, RoleRow.scope_id)
                .where(
                    RoleRow.role_preset_id == preset_id,
                    RoleRow.scope_type == scope_type,
                )
                .order_by(RoleRow.id)
            )
        ).all()
        return [
            (role_id, RuntimeEntityID(EntityType(scope_type), scope_id))
            for role_id, scope_id in rows
        ]

    async def _held_entity_types(self, role_ids: Sequence[RoleID]) -> dict[RoleID, set[EntityType]]:
        """The entity types each role currently holds permissions on."""
        rows = (
            await self._sess.execute(
                sa.select(PermissionRow.role_id, PermissionRow.entity_type).where(
                    PermissionRow.role_id.in_(list(role_ids))
                )
            )
        ).all()
        held: dict[RoleID, set[EntityType]] = {}
        for role_id, entity_type in rows:
            held.setdefault(RoleID(role_id), set()).add(EntityType(entity_type))
        return held

    async def _rendered_names(
        self,
        preset: RolePresetRow,
        scope_type: EntityType,
        entities: Mapping[RoleID, EntityIdentifier],
    ) -> dict[RoleID, str]:
        """The name the preset's rule now yields per role; a templated preset whose
        scope row is gone leaves that role's name alone."""
        if preset.role_name_template is None:
            return {
                role_id: self._default_preset_role_name(preset, entity)
                for role_id, entity in entities.items()
            }
        values = await self._scope_template_values(scope_type, entities.values())
        return {
            role_id: self._preset_role_name(preset, entity, values[entity])
            for role_id, entity in entities.items()
            if entity in values
        }

    async def _scope_template_values(
        self, scope_type: EntityType, scopes: Collection[EntityIdentifier]
    ) -> dict[EntityIdentifier, ScopeTemplateValue]:
        row_cls = self._scope_rows.get(scope_type)
        if row_cls is None:
            return {}
        rows = (
            await self._sess.execute(
                sa.select(row_cls.scope_id_expr(), row_cls.scope_name_expr()).where(
                    row_cls.scope_id_expr().in_(list(scopes))
                )
            )
        ).all()
        by_id = {scope: scope for scope in scopes}
        return {
            by_id[scope_id]: ScopeTemplateValue(id=scope_id, name=name, type=str(scope_type))
            for scope_id, name in rows
            if scope_id in by_id
        }
