import uuid
from dataclasses import dataclass
from typing import Self

from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesCreateInput,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.role import RoleCreateInput
from ai.backend.manager.data.permission.scope_permission import ScopePermissionCreateInput
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.data.permission.user_role import UserRoleCreateInput
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.user import UserRole, UserRow

from .types import PermissionCreateInputGroup

ROLE_NAME_PREFIX = "role_"


@dataclass
class ProjectData:
    id: uuid.UUID

    @classmethod
    def from_row(cls, group_row: GroupRow) -> Self:
        return cls(id=group_row.id)

    @property
    def role_name(self) -> str:
        return f"{ROLE_NAME_PREFIX}project_{str(self.id)[:8]}"

    def to_rbac_input_data(self) -> PermissionCreateInputGroup:
        role_id = uuid.uuid4()
        return PermissionCreateInputGroup(
            roles=[
                RoleCreateInput(
                    name=self.role_name,
                    id=role_id,
                )
            ],
            scope_permissions=[
                ScopePermissionCreateInput(
                    role_id=role_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(self.id),
                    entity_type=EntityType.USER,
                    operation=OperationType.READ,
                ),
            ],
        )


@dataclass
class UserData:
    id: uuid.UUID
    username: str
    domain: str
    role: UserRole

    @property
    def role_name(self) -> str:
        return f"{ROLE_NAME_PREFIX}user_{self.username}"

    @classmethod
    def from_row(cls, user_row: UserRow) -> Self:
        return cls(
            id=user_row.uuid,
            username=user_row.username,
            domain=user_row.domain_name,
            role=user_row.role,
        )

    def to_rbac_input_data(self) -> PermissionCreateInputGroup:
        role_id = uuid.uuid4()
        scope_permissions: list[ScopePermissionCreateInput] = [
            ScopePermissionCreateInput(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=str(self.id),
                entity_type=EntityType.USER,
                operation=OperationType.READ,
            ),
            ScopePermissionCreateInput(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=str(self.id),
                entity_type=EntityType.USER,
                operation=OperationType.UPDATE,
            ),
            ScopePermissionCreateInput(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=str(self.id),
                entity_type=EntityType.USER,
                operation=OperationType.SOFT_DELETE,
            ),
            ScopePermissionCreateInput(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=str(self.id),
                entity_type=EntityType.USER,
                operation=OperationType.GRANT_ALL,
            ),
            ScopePermissionCreateInput(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=str(self.id),
                entity_type=EntityType.USER,
                operation=OperationType.GRANT_READ,
            ),
            ScopePermissionCreateInput(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=str(self.id),
                entity_type=EntityType.USER,
                operation=OperationType.GRANT_UPDATE,
            ),
            ScopePermissionCreateInput(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=str(self.id),
                entity_type=EntityType.USER,
                operation=OperationType.GRANT_SOFT_DELETE,
            ),
        ]
        return PermissionCreateInputGroup(
            roles=[
                RoleCreateInput(
                    name=self.role_name,
                    id=role_id,
                )
            ],
            user_roles=[
                UserRoleCreateInput(
                    user_id=self.id,
                    role_id=role_id,
                )
            ],
            scope_permissions=scope_permissions,
        )


def user_row_to_rbac_migration_data(user_row: UserRow) -> PermissionCreateInputGroup:
    data = UserData.from_row(user_row)
    return data.to_rbac_input_data()


def project_row_to_rbac_migration_data(project_row: GroupRow) -> PermissionCreateInputGroup:
    data = ProjectData.from_row(project_row)
    return data.to_rbac_input_data()


def map_role_to_project(role_id: uuid.UUID, group_row: GroupRow) -> PermissionCreateInputGroup:
    user_roles: list[UserRoleCreateInput] = []
    association_scopes_entities: list[AssociationScopesEntitiesCreateInput] = []
    for association_row in group_row.users:
        user_roles.append(
            UserRoleCreateInput(
                user_id=association_row.user_id,
                role_id=role_id,
            )
        )
        association_scopes_entities.append(
            AssociationScopesEntitiesCreateInput(
                scope_id=ScopeId(
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(group_row.id),
                ),
                object_id=ObjectId(
                    entity_type=EntityType.USER,
                    entity_id=str(association_row.user_id),
                ),
            )
        )
    return PermissionCreateInputGroup(
        user_roles=user_roles,
        association_scopes_entities=association_scopes_entities,
    )
