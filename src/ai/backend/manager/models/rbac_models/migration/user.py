import enum
import uuid
from dataclasses import dataclass
from typing import Self

from sqlalchemy.engine.row import Row

from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesCreateInput,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.role import RoleCreateInput
from ai.backend.manager.data.permission.scope_permission import ScopePermissionCreateInput
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.data.permission.user_role import UserRoleCreateInput

from .types import (
    ADMIN_ROLE_NAME_SUFFIX,
    ROLE_NAME_PREFIX,
    PermissionCreateInputGroup,
    is_admin_role,
)

USER_SELF_SCOPE_OPERATIONS = (
    OperationType.READ,
    OperationType.UPDATE,
    OperationType.SOFT_DELETE,
    OperationType.GRANT_ALL,
    OperationType.GRANT_READ,
    OperationType.GRANT_UPDATE,
)
ADMIN_OPERATIONS = (
    OperationType.CREATE,
    OperationType.READ,
    OperationType.UPDATE,
    OperationType.SOFT_DELETE,
    OperationType.HARD_DELETE,
    OperationType.GRANT_ALL,
    OperationType.GRANT_READ,
    OperationType.GRANT_UPDATE,
    OperationType.GRANT_SOFT_DELETE,
    OperationType.GRANT_HARD_DELETE,
)


class UserRole(enum.StrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


class RoleNameUtil:
    @staticmethod
    def user_role_name(user: "UserData") -> str:
        """
        Generate a role name for a user.
        """
        return f"{ROLE_NAME_PREFIX}user_{user.username}"

    @staticmethod
    def project_role_name(project: "ProjectData", is_admin: bool) -> str:
        """
        Generate a role name for a project.
        """
        role_type = ADMIN_ROLE_NAME_SUFFIX if is_admin else "_user"
        return f"{ROLE_NAME_PREFIX}project_{str(project.id)[:8]}{role_type}"

    @staticmethod
    def is_admin_role(role_name: str) -> bool:
        """
        Check if the role name indicates an admin role.
        """
        return is_admin_role(role_name)


@dataclass
class ProjectData:
    id: uuid.UUID

    def role_name(self, is_admin: bool) -> str:
        return RoleNameUtil.project_role_name(self, is_admin)

    @classmethod
    def from_row(cls, group_row: Row) -> Self:
        return cls(id=group_row.id)


@dataclass
class UserData:
    id: uuid.UUID
    username: str
    domain: str
    role: UserRole

    def role_name(self) -> str:
        return RoleNameUtil.user_role_name(self)

    @classmethod
    def from_row(cls, user_row: Row) -> Self:
        return cls(
            id=user_row.uuid,
            username=user_row.username,
            domain=user_row.domain_name,
            role=user_row.role,
        )


@dataclass
class ProjectUserAssociationData:
    project_id: uuid.UUID
    user_id: uuid.UUID


def create_user_self_role_and_permissions(user: UserData) -> PermissionCreateInputGroup:
    """
    Create a self role and permissions for a user.
    This role allows the user to manage their own data.
    """
    role_id = uuid.uuid4()
    role_input = RoleCreateInput(
        name=user.role_name(),
        source=RoleSource.SYSTEM,
        id=role_id,
    )
    scope_permission_inputs: list[ScopePermissionCreateInput] = [
        ScopePermissionCreateInput(
            role_id=role_id,
            scope_type=ScopeType.USER,
            scope_id=str(user.id),
            entity_type=EntityType.USER,
            operation=operation,
        )
        for operation in USER_SELF_SCOPE_OPERATIONS
    ]
    user_role_input = UserRoleCreateInput(
        user_id=user.id,
        role_id=role_id,
    )
    return PermissionCreateInputGroup(
        roles=[role_input],
        user_roles=[user_role_input],
        scope_permissions=scope_permission_inputs,
    )


def create_project_admin_role_and_permissions(project: ProjectData) -> PermissionCreateInputGroup:
    """
    Create an admin role and permissions for a project.
    This role allows the user to manage the project.
    """
    role_id = uuid.uuid4()
    role_input = RoleCreateInput(
        name=project.role_name(is_admin=True),
        source=RoleSource.SYSTEM,
        id=role_id,
    )
    scope_permission_inputs: list[ScopePermissionCreateInput] = [
        ScopePermissionCreateInput(
            role_id=role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=str(project.id),
            entity_type=EntityType.USER,
            operation=operation,
        )
        for operation in ADMIN_OPERATIONS
    ]
    return PermissionCreateInputGroup(
        roles=[role_input],
        scope_permissions=scope_permission_inputs,
    )


def create_project_user_role_and_permissions(project: ProjectData) -> PermissionCreateInputGroup:
    """
    Create a user role and permissions for a project.
    This role allows the user to read the project.
    """
    role_id = uuid.uuid4()
    role_input = RoleCreateInput(
        name=project.role_name(is_admin=False),
        source=RoleSource.SYSTEM,
        id=role_id,
    )
    scope_permission_inputs: list[ScopePermissionCreateInput] = [
        ScopePermissionCreateInput(
            role_id=role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=str(project.id),
            entity_type=EntityType.USER,
            operation=OperationType.READ,
        )
    ]
    return PermissionCreateInputGroup(
        roles=[role_input],
        scope_permissions=scope_permission_inputs,
    )


def map_user_to_project_role(
    role_id: uuid.UUID, association: ProjectUserAssociationData
) -> PermissionCreateInputGroup:
    """
    Map a user to a project role.
    This is used when a user is assigned to a project.
    """
    user_role_input = UserRoleCreateInput(
        user_id=association.user_id,
        role_id=role_id,
    )
    association_input = AssociationScopesEntitiesCreateInput(
        scope_id=ScopeId(
            scope_type=ScopeType.PROJECT,
            scope_id=str(association.project_id),
        ),
        object_id=ObjectId(
            entity_type=EntityType.USER,
            entity_id=str(association.user_id),
        ),
    )
    return PermissionCreateInputGroup(
        user_roles=[user_role_input],
        association_scopes_entities=[association_input],
    )
