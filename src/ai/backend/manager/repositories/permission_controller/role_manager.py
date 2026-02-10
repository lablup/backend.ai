import logging
import uuid
from collections.abc import Iterable, Mapping
from typing import Protocol, cast

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession as SASession

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
    RoleSource,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.permission_controller.creators import (
    AssociationScopesEntitiesCreatorSpec,
    ObjectPermissionCreatorSpec,
    RoleCreatorSpec,
)

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
        await self._create_permissions(db_session, data)
        return role

    async def _create_system_role(
        self, db_session: SASession, data: ScopeSystemRoleData
    ) -> RoleData:
        creator = Creator(
            spec=RoleCreatorSpec(
                name=data.role_name(),
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
            )
        )
        result = await execute_creator(db_session, creator)
        return result.row.to_data()

    async def _create_permissions(
        self,
        db_session: SASession,
        data: ScopeSystemRoleData,
    ) -> list[PermissionData]:
        permission_rows: list[PermissionRow] = []
        for entity, operations in data.entity_operations().items():
            for operation in operations:
                creator = PermissionCreator(
                    entity_type=entity,
                    operation=operation,
                )
                permission_rows.append(PermissionRow.from_input(creator))
        db_session.add_all(permission_rows)
        await db_session.flush()
        return [row.to_data() for row in permission_rows]

    async def map_user_to_role(self, db_session: SASession, creator: Creator[UserRoleRow]) -> None:
        await execute_creator(db_session, creator)

    async def map_entity_to_scope(
        self,
        db_session: SASession,
        creator: Creator[AssociationScopesEntitiesRow],
    ) -> None:
        try:
            await execute_creator(db_session, creator)
        except IntegrityError:
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
                    entity_type=entity_id.entity_type,
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
