import logging
import uuid
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.permission import PermissionCreator, PermissionData
from ai.backend.manager.data.permission.role import (
    RoleData,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RBACElementRef,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.errors.repository import RepositoryIntegrityError
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.permission_controller.creators import (
    AssociationScopesEntitiesCreatorSpec,
    ObjectPermissionCreatorSpec,
    RoleCreatorSpec,
    UserRoleCreatorSpec,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class ScopeSystemRoleData(Protocol):
    def scope_id(self) -> ScopeId: ...

    def role_name(self) -> str: ...

    def entity_operations(self) -> Mapping[RBACElementType, Iterable[OperationType]]:
        """Returns a mapping of entity types to the set of operations that should be granted for each entity type."""
        ...


@dataclass(frozen=True)
class UserSystemRoleSpec:
    """Minimal implementation of ScopeSystemRoleData for user system role creation."""

    user_id: uuid.UUID

    def scope_id(self) -> ScopeId:
        return ScopeId(scope_type=ScopeType.USER, scope_id=str(self.user_id))

    def role_name(self) -> str:
        return f"user-{str(self.user_id)[:8]}"

    def entity_operations(self) -> Mapping[RBACElementType, Iterable[OperationType]]:
        resource_entity_permissions = {
            entity.to_element(): OperationType.owner_operations()
            for entity in EntityType.owner_accessible_entity_types_in_user()
        }
        user_permissions = OperationType.owner_operations() - {OperationType.CREATE}
        return {RBACElementType.USER: user_permissions, **resource_entity_permissions}


class RoleManager:
    def __init__(self) -> None:
        pass

    async def create_system_role(
        self, db_session: SASession, data: ScopeSystemRoleData
    ) -> RoleData:
        role = await self._create_system_role(db_session, data)
        await self._create_permissions(db_session, data, role.id)
        return role

    async def _create_system_role(
        self, db_session: SASession, data: ScopeSystemRoleData
    ) -> RoleData:
        scope_id = data.scope_id()
        rbac_creator = RBACEntityCreator(
            spec=RoleCreatorSpec(
                name=data.role_name(),
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
            ),
            element_type=RBACElementType.ROLE,
            scope_ref=RBACElementRef(
                element_type=scope_id.scope_type.to_element(),
                element_id=scope_id.scope_id,
            ),
        )
        result = await execute_rbac_entity_creator(db_session, rbac_creator)
        return result.row.to_data()

    async def _create_permissions(
        self,
        db_session: SASession,
        data: ScopeSystemRoleData,
        role_id: uuid.UUID,
    ) -> list[PermissionData]:
        permission_rows: list[PermissionRow] = []
        for element_type, operations in data.entity_operations().items():
            for operation in operations:
                creator = PermissionCreator(
                    role_id=role_id,
                    scope_type=data.scope_id().scope_type,
                    scope_id=data.scope_id().scope_id,
                    entity_type=element_type.to_entity_type(),
                    operation=operation,
                )
                permission_rows.append(PermissionRow.from_input(creator))
        db_session.add_all(permission_rows)
        await db_session.flush()
        return [row.to_data() for row in permission_rows]

    async def create_preset_roles(self, db_session: SASession, scope_id: ScopeId) -> list[RoleData]:
        """Auto-generate roles from active role presets matching the given scope."""
        preset_rows = (
            await db_session.scalars(
                sa.select(RolePresetRow).where(
                    sa.and_(
                        RolePresetRow.scope_type == scope_id.scope_type,
                        RolePresetRow.deleted.is_(False),
                    )
                )
            )
        ).all()
        if not preset_rows:
            return []
        permission_presets_by_preset = await self._fetch_permission_presets(
            db_session, [preset.id for preset in preset_rows]
        )
        created_roles: list[RoleData] = []
        for preset in preset_rows:
            role = await self._create_preset_role(
                db_session,
                scope_id,
                preset,
                permission_presets_by_preset.get(preset.id, []),
            )
            created_roles.append(role)
        return created_roles

    async def _fetch_permission_presets(
        self,
        db_session: SASession,
        preset_ids: list[RolePresetID],
    ) -> dict[RolePresetID, list[RolePermissionPresetRow]]:
        permission_preset_rows = (
            await db_session.scalars(
                sa.select(RolePermissionPresetRow).where(
                    RolePermissionPresetRow.role_preset_id.in_(preset_ids)
                )
            )
        ).all()
        grouped: dict[RolePresetID, list[RolePermissionPresetRow]] = defaultdict(list)
        for row in permission_preset_rows:
            grouped[row.role_preset_id].append(row)
        return grouped

    async def _create_preset_role(
        self,
        db_session: SASession,
        scope_id: ScopeId,
        preset: RolePresetRow,
        permission_presets: list[RolePermissionPresetRow],
    ) -> RoleData:
        rbac_creator = RBACEntityCreator(
            spec=RoleCreatorSpec(
                name=preset.name,
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                auto_assign=preset.auto_assign,
            ),
            element_type=RBACElementType.ROLE,
            scope_ref=RBACElementRef(
                element_type=scope_id.scope_type.to_element(),
                element_id=scope_id.scope_id,
            ),
        )
        result = await execute_rbac_entity_creator(db_session, rbac_creator)
        role = result.row.to_data()
        await self._create_preset_permissions(db_session, scope_id, role.id, permission_presets)
        return role

    async def _create_preset_permissions(
        self,
        db_session: SASession,
        scope_id: ScopeId,
        role_id: uuid.UUID,
        permission_presets: list[RolePermissionPresetRow],
    ) -> None:
        if not permission_presets:
            return
        permission_rows = [
            PermissionRow.from_input(
                PermissionCreator(
                    role_id=role_id,
                    scope_type=scope_id.scope_type,
                    scope_id=scope_id.scope_id,
                    entity_type=preset_permission.entity_type,
                    operation=preset_permission.operation,
                )
            )
            for preset_permission in permission_presets
        ]
        db_session.add_all(permission_rows)
        await db_session.flush()

    async def create_preset_roles_for_user(
        self, db_session: SASession, user_id: uuid.UUID
    ) -> list[RoleData]:
        """Provision user-scope preset roles for a newly created user.

        Creates the roles from active user-scope presets (see `create_preset_roles`)
        and assigns the auto_assign ones to the user, who is the sole member of its
        own user scope. Returns all created roles.
        """
        scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(user_id))
        created_roles = await self.create_preset_roles(db_session, scope_id)
        for role in created_roles:
            if not role.auto_assign:
                continue
            await self.map_user_to_role(
                db_session,
                Creator(spec=UserRoleCreatorSpec(user_id=user_id, role_id=role.id)),
            )
        return created_roles

    async def map_user_to_role(self, db_session: SASession, creator: Creator[UserRoleRow]) -> None:
        await execute_creator(db_session, creator)

    async def map_entity_to_scope(
        self,
        db_session: SASession,
        creator: Creator[AssociationScopesEntitiesRow],
    ) -> None:
        try:
            await execute_creator(db_session, creator)
        except RepositoryIntegrityError:
            spec = cast(AssociationScopesEntitiesCreatorSpec, creator.spec)
            log.exception(
                "entity and scope mapping already exists: {}, {}. Skipping.",
                spec.object_id.to_str(),
                spec.scope_id.to_str(),
            )

    async def unmap_entity_from_scope(
        self,
        db_session: SASession,
        entity_id: ObjectId,
        scope_id: ScopeId,
    ) -> None:
        await db_session.execute(
            sa.delete(AssociationScopesEntitiesRow).where(
                sa.and_(
                    AssociationScopesEntitiesRow.scope_type == scope_id.scope_type,
                    AssociationScopesEntitiesRow.scope_id == scope_id.scope_id,
                    AssociationScopesEntitiesRow.entity_type == entity_id.entity_type,
                    AssociationScopesEntitiesRow.entity_id == entity_id.entity_id,
                )
            )
        )

    async def add_object_permission_to_user_role(
        self,
        db_session: SASession,
        user_id: uuid.UUID,
        entity_id: ObjectId,
        operations: Iterable[OperationType],
    ) -> list[ObjectPermissionData]:
        role_row = await db_session.scalar(
            sa.select(RoleRow)
            .join(UserRoleRow, UserRoleRow.role_id == RoleRow.id)
            .where(UserRoleRow.user_id == user_id)
        )
        if role_row is None:
            raise ValueError(f"Role not found for user_id={user_id}")
        role_id = role_row.id

        creators = [
            Creator(
                spec=ObjectPermissionCreatorSpec(
                    role_id=role_id,
                    entity_type=entity_id.entity_type.to_element(),
                    entity_id=entity_id.entity_id,
                    operation=operation,
                )
            )
            for operation in operations
        ]

        results = [await execute_creator(db_session, creator) for creator in creators]
        return [result.row.to_data() for result in results]

    async def delete_object_permission_of_user(
        self,
        db_session: SASession,
        user_id: uuid.UUID,
        entity_id: uuid.UUID,
    ) -> None:
        role_row = await db_session.scalar(
            sa.select(RoleRow)
            .join(UserRoleRow, UserRoleRow.role_id == RoleRow.id)
            .where(UserRoleRow.user_id == user_id)
        )
        if role_row is None:
            raise ValueError(f"Role not found for user_id={user_id}")
        role_id = role_row.id
        await db_session.execute(
            sa.delete(ObjectPermissionRow).where(
                sa.and_(
                    ObjectPermissionRow.role_id == role_id,
                    ObjectPermissionRow.entity_id == str(entity_id),
                )
            )
        )
