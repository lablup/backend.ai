import logging
import uuid
from collections.abc import Collection, Iterable, Mapping
from typing import Optional, Protocol, cast

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesCreateInput,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.object_permission import (
    ObjectPermissionCreateInput,
)
from ai.backend.manager.data.permission.permission import PermissionCreator, PermissionData
from ai.backend.manager.data.permission.permission_group import (
    PermissionGroupCreator,
    PermissionGroupData,
)
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
)
from ai.backend.manager.data.permission.user_role import UserRoleCreateInput
from ai.backend.manager.errors.rbac import RoleNotFound, UserSystemRoleNotFound
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow

from ...data.permission.role import (
    RoleCreateInput,
    RoleData,
    RoleDataWithPermissions,
)
from ...models.rbac_models.role import RoleRow

log = BraceStyleAdapter(logging.getLogger(__name__))


class ScopeSystemRoleData(Protocol):
    def scope_id(self) -> ScopeId: ...

    def role_name(self) -> str: ...

    def entity_operations(self) -> Mapping[EntityType, Iterable[OperationType]]:
        """Returns a mapping of entity types to the set of operations that should be granted for each entity type."""
        ...


class RoleManager:
    def __init__(self) -> None:
        pass

    async def create_system_role(
        self, db_session: SASession, data: ScopeSystemRoleData
    ) -> RoleData:
        role = await self._create_system_role(db_session, data)
        permission_group = await self._create_permission_group(db_session, data, role)
        await self._create_permissions(db_session, data, permission_group)
        return role

    async def _create_system_role(
        self, db_session: SASession, data: ScopeSystemRoleData
    ) -> RoleData:
        input = RoleCreateInput(
            name=data.role_name(),
            source=RoleSource.SYSTEM,
        )
        row = RoleRow.from_input(input)
        db_session.add(row)
        await db_session.flush()
        await db_session.refresh(row)
        return row.to_data()

    async def _create_permission_group(
        self, db_session: SASession, data: ScopeSystemRoleData, role: RoleData
    ) -> PermissionGroupData:
        input = PermissionGroupCreator(
            role_id=role.id,
            scope_id=data.scope_id(),
        )
        row = PermissionGroupRow.from_input(input)
        db_session.add(row)
        await db_session.flush()
        await db_session.refresh(row)
        return row.to_data()

    async def _create_permissions(
        self,
        db_session: SASession,
        data: ScopeSystemRoleData,
        permission_group: PermissionGroupData,
    ) -> list[PermissionData]:
        permission_rows: list[PermissionRow] = []
        for entity, operations in data.entity_operations().items():
            for operation in operations:
                creator = PermissionCreator(
                    permission_group_id=permission_group.id,
                    entity_type=entity,
                    operation=operation,
                )
                permission_rows.append(PermissionRow.from_input(creator))
        db_session.add_all(permission_rows)
        await db_session.flush()
        return [row.to_data() for row in permission_rows]

    async def map_user_to_role(
        self, db_session: SASession, user_id: uuid.UUID, role_id: uuid.UUID
    ) -> None:
        creator = UserRoleCreateInput(
            user_id=user_id,
            role_id=role_id,
        )
        await db_session.execute(sa.insert(UserRoleRow).values(creator.fields_to_store()))

    async def map_entity_to_scope(
        self,
        db_session: SASession,
        entity_id: ObjectId,
        scope_id: ScopeId,
    ) -> None:
        creator = AssociationScopesEntitiesCreateInput(
            scope_id=scope_id,
            object_id=entity_id,
        )
        try:
            await db_session.execute(
                sa.insert(AssociationScopesEntitiesRow).values(creator.fields_to_store())
            )
        except IntegrityError:
            log.exception(
                "entity and scope mapping already exists: {}, {}. Skipping.",
                entity_id.to_str(),
                scope_id.to_str(),
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
        operations: Collection[OperationType],
    ) -> RoleDataWithPermissions:
        """
        Adds object permissions to the system role mapped to the user
        and adds permission groups for the scopes associated with the entity if not already present in the role.

        Returns the updated role with permissions.
        Raises an exception if the user does not have a system role.
        """

        role = await self._query_system_role_by_user(db_session, user_id)
        entity_associated_scopes = await self._query_entity_associated_scopes(db_session, entity_id)
        await self._add_permission_groups_to_role_if_not_exist(
            db_session, role, entity_associated_scopes
        )
        await self._add_object_permissions_to_role(db_session, role.id, entity_id, operations)
        updated_role = await self._query_role_by_id(db_session, role.id)
        return updated_role

    async def _query_system_role_by_user(
        self,
        db_session: SASession,
        user_id: uuid.UUID,
    ) -> RoleRow:
        role_row = await db_session.scalar(
            sa.select(RoleRow)
            .select_from(sa.join(RoleRow, UserRoleRow, RoleRow.id == UserRoleRow.role_id))
            .where(sa.and_(UserRoleRow.user_id == user_id, RoleRow.source == RoleSource.SYSTEM))
            .options(selectinload(RoleRow.permission_group_rows))
        )
        role_row = cast(Optional[RoleRow], role_row)
        if role_row is None:
            raise UserSystemRoleNotFound(f"System role for user {user_id} not found")
        return role_row

    async def _query_role_by_id(
        self,
        db_session: SASession,
        role_id: uuid.UUID,
    ) -> RoleDataWithPermissions:
        role_row = await db_session.scalar(
            sa.select(RoleRow)
            .where(RoleRow.id == role_id)
            .options(
                selectinload(RoleRow.permission_group_rows).options(
                    selectinload(PermissionGroupRow.permission_rows)
                ),
                selectinload(RoleRow.object_permission_rows),
            )
        )
        role_row = cast(Optional[RoleRow], role_row)
        if role_row is None:
            raise RoleNotFound(f"Role with id {role_id} not found")
        return role_row

    async def _query_entity_associated_scopes(
        self,
        db_session: SASession,
        entity_id: ObjectId,
    ) -> list[ScopeId]:
        raw_scope_entity_rows = await db_session.scalars(
            sa.select(AssociationScopesEntitiesRow).where(
                sa.and_(
                    AssociationScopesEntitiesRow.entity_type == entity_id.entity_type,
                    AssociationScopesEntitiesRow.entity_id == entity_id.entity_id,
                )
            )
        )
        scope_entity_rows = cast(list[AssociationScopesEntitiesRow], raw_scope_entity_rows.all())
        return [
            ScopeId(scope_type=row.scope_type, scope_id=row.scope_id) for row in scope_entity_rows
        ]

    async def _add_permission_groups_to_role_if_not_exist(
        self,
        db_session: SASession,
        role_row: RoleRow,
        scope_ids: Collection[ScopeId],
    ) -> None:
        scope_ids_to_add = {scope for scope in scope_ids}
        for permission_group in role_row.permission_group_rows:
            scope_id = permission_group.parsed_scope_id()
            scope_ids_to_add.discard(scope_id)
        creators = [
            PermissionGroupCreator(
                role_id=role_row.id,
                scope_id=scope_id,
            )
            for scope_id in scope_ids_to_add
        ]

        rows = [PermissionGroupRow.from_input(creator) for creator in creators]
        db_session.add_all(rows)
        await db_session.flush()

    async def _add_object_permissions_to_role(
        self,
        db_session: SASession,
        role_id: uuid.UUID,
        entity_id: ObjectId,
        operations: Collection[OperationType],
    ) -> None:
        if not operations:
            log.warning(
                "no operations provided to add object permissions to role {}, skipping.", role_id
            )
            return
        creators = [
            ObjectPermissionCreateInput(
                role_id=role_id,
                entity_type=entity_id.entity_type,
                entity_id=entity_id.entity_id,
                operation=operation,
            )
            for operation in operations
        ]

        rows = [ObjectPermissionRow.from_input(creator) for creator in creators]
        db_session.add_all(rows)
        await db_session.flush()

    async def delete_object_permission_of_user(
        self,
        db_session: SASession,
        user_id: uuid.UUID,
        entity_id: uuid.UUID,
    ) -> None:
        permission_group = await db_session.scalar(
            sa.select(PermissionGroupRow).where(PermissionGroupRow.scope_id == str(user_id))
        )
        role_id = permission_group.role_id
        await db_session.execute(
            sa.delete(ObjectPermissionRow).where(
                sa.and_(
                    ObjectPermissionRow.role_id == role_id,
                    ObjectPermissionRow.entity_id == str(entity_id),
                )
            )
        )
