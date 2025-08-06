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
from ai.backend.manager.models.user import UserRole, UserRow

from .types import PermissionCreateInputGroup

ROLE_NAME_PREFIX = "role_"


@dataclass
class ProjectData:
    id: uuid.UUID


@dataclass
class UserData:
    id: uuid.UUID
    username: str
    domain: str
    role: UserRole
    registered_projects: list[ProjectData]

    @classmethod
    def from_user_row(cls, user_row: UserRow) -> Self:
        return cls(
            id=user_row.uuid,
            username=user_row.username,
            domain=user_row.domain_name,
            role=user_row.role,
            registered_projects=[ProjectData(id=assoc.group_id) for assoc in user_row.groups],
        )

    def to_role_create_input(self) -> PermissionCreateInputGroup:
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
        association_scopes_entities: list[AssociationScopesEntitiesCreateInput] = []
        for project in self.registered_projects:
            scope_permissions.append(
                ScopePermissionCreateInput(
                    role_id=role_id,
                    scope_type=ScopeType.PROJECT,
                    scope_id=str(project.id),
                    entity_type=EntityType.USER,
                    operation=OperationType.READ,
                )
            )
            association_scopes_entities.append(
                AssociationScopesEntitiesCreateInput(
                    scope_id=ScopeId(
                        scope_type=ScopeType.PROJECT,
                        scope_id=str(project.id),
                    ),
                    object_id=ObjectId(
                        entity_type=EntityType.USER,
                        entity_id=str(self.id),
                    ),
                )
            )
        return PermissionCreateInputGroup(
            roles=[
                RoleCreateInput(
                    name=f"{ROLE_NAME_PREFIX}{self.username}",
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
            association_scopes_entities=association_scopes_entities,
        )


def user_row_to_rbac_migration_data(user_row: UserRow) -> PermissionCreateInputGroup:
    data = UserData.from_user_row(user_row)
    return data.to_role_create_input()
