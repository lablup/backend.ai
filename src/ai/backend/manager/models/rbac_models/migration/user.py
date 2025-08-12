import enum
import uuid
from dataclasses import dataclass
from typing import Optional, Self

from sqlalchemy.engine.row import Row

from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from .enums import (
    EntityType,
    RoleSource,
    ScopeType,
)
from .types import (
    ADMIN_ROLE_NAME_SUFFIX,
    ROLE_NAME_PREFIX,
    AssociationScopesEntitiesCreateInput,
    RoleCreateInput,
    UserRoleCreateInput,
    UserRoleMappingInputGroup,
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

        'role_project_<project_id>_admin' for admin roles.
        'role_project_<project_id>_member' for member roles.
        """
        role_type = ADMIN_ROLE_NAME_SUFFIX if is_admin else "_member"
        return f"{ROLE_NAME_PREFIX}project_{str(project.id)[:8]}{role_type}"

    @staticmethod
    def domain_role_name(domain: "DomainData", is_admin: bool) -> str:
        """
        Generate a role name for a domain.

        'role_domain_<domain_name>_admin' for admin roles.
        'role_domain_<domain_name>_member' for member roles.
        """
        role_type = ADMIN_ROLE_NAME_SUFFIX if is_admin else "_member"
        return f"{ROLE_NAME_PREFIX}domain_{domain.name}{role_type}"


@dataclass
class DomainData:
    name: str

    def role_name(self, is_admin: bool) -> str:
        return RoleNameUtil.domain_role_name(self, is_admin)

    @classmethod
    def from_row(cls, domain_row: Row) -> Self:
        return cls(name=domain_row.name)


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


def get_user_self_role_creation_input(user: UserData) -> RoleCreateInput:
    """
    Create a self role and permissions for a user.
    This role allows the user to manage their own data.
    """
    role_input = RoleCreateInput(
        name=user.role_name(),
        source=RoleSource.SYSTEM,
    )
    return role_input


def get_project_admin_role_creation_input(project: ProjectData) -> RoleCreateInput:
    """
    Create an admin role for a project.
    This role allows the user to manage the project.
    """
    return RoleCreateInput(
        name=project.role_name(is_admin=True),
        source=RoleSource.SYSTEM,
    )


def get_project_member_role_creation_input(project: ProjectData) -> RoleCreateInput:
    """
    Create a member role for a project.
    This role allows the user to read the project.
    """
    return RoleCreateInput(
        name=project.role_name(is_admin=False),
        source=RoleSource.CUSTOM,
    )


def get_domain_admin_role_creation_input(domain: DomainData) -> RoleCreateInput:
    """
    Create an admin role for a domain.
    This role allows the user to manage the domain.
    """
    return RoleCreateInput(
        name=domain.role_name(is_admin=True),
        source=RoleSource.SYSTEM,
    )


def get_domain_member_role_creation_input(domain: DomainData) -> RoleCreateInput:
    """
    Create an admin role for a domain.
    This role allows the user to manage the domain.
    """
    return RoleCreateInput(
        name=domain.role_name(is_admin=False),
        source=RoleSource.CUSTOM,
    )


@dataclass
class UserScopeRoleMappingArgs:
    user_id: uuid.UUID
    user_role: UserRole

    scope_id: ScopeId
    role_id: uuid.UUID
    role_source: RoleSource


def get_user_project_mapping_creation_input(
    args: UserScopeRoleMappingArgs,
) -> Optional[UserRoleMappingInputGroup]:
    result: Optional[UserRoleMappingInputGroup] = None
    match args.user_role:
        case UserRole.SUPERADMIN | UserRole.MONITOR:
            pass
        case UserRole.ADMIN:
            if args.role_source == RoleSource.SYSTEM:
                user_role_mapping_input = UserRoleCreateInput(
                    user_id=args.user_id, role_id=args.role_id
                )
                associtation_input = AssociationScopesEntitiesCreateInput(
                    scope_id=ScopeId(
                        scope_type=ScopeType.PROJECT.to_original(),
                        scope_id=args.scope_id.scope_id,
                    ),
                    object_id=ObjectId(
                        entity_type=EntityType.USER.to_original(),
                        entity_id=str(args.user_id),
                    ),
                )
                result = UserRoleMappingInputGroup(
                    user_role_input=user_role_mapping_input,
                    association_scopes_entities_input=associtation_input,
                )
        case UserRole.USER:
            if args.role_source == RoleSource.CUSTOM:
                user_role_mapping_input = UserRoleCreateInput(
                    user_id=args.user_id, role_id=args.role_id
                )
                associtation_input = AssociationScopesEntitiesCreateInput(
                    scope_id=ScopeId(
                        scope_type=ScopeType.PROJECT.to_original(),
                        scope_id=args.scope_id.scope_id,
                    ),
                    object_id=ObjectId(
                        entity_type=EntityType.USER.to_original(),
                        entity_id=str(args.user_id),
                    ),
                )
                result = UserRoleMappingInputGroup(
                    user_role_input=user_role_mapping_input,
                    association_scopes_entities_input=associtation_input,
                )
    return result


def get_user_domain_mapping_creation_input(
    args: UserScopeRoleMappingArgs,
) -> Optional[UserRoleMappingInputGroup]:
    """
    Map a user to a domain role and a domain scope.

    """
    result: Optional[UserRoleMappingInputGroup] = None
    match args.user_role:
        case UserRole.SUPERADMIN | UserRole.MONITOR:
            pass
        case UserRole.ADMIN:
            if args.role_source == RoleSource.SYSTEM:
                user_role_mapping_input = UserRoleCreateInput(
                    user_id=args.user_id, role_id=args.role_id
                )
                associtation_input = AssociationScopesEntitiesCreateInput(
                    scope_id=ScopeId(
                        scope_type=ScopeType.DOMAIN.to_original(),
                        scope_id=args.scope_id.scope_id,
                    ),
                    object_id=ObjectId(
                        entity_type=EntityType.USER.to_original(),
                        entity_id=str(args.user_id),
                    ),
                )
                result = UserRoleMappingInputGroup(
                    user_role_input=user_role_mapping_input,
                    association_scopes_entities_input=associtation_input,
                )
        case UserRole.USER:
            if args.role_source == RoleSource.CUSTOM:
                user_role_mapping_input = UserRoleCreateInput(
                    user_id=args.user_id, role_id=args.role_id
                )
                associtation_input = AssociationScopesEntitiesCreateInput(
                    scope_id=ScopeId(
                        scope_type=ScopeType.DOMAIN.to_original(),
                        scope_id=args.scope_id.scope_id,
                    ),
                    object_id=ObjectId(
                        entity_type=EntityType.USER.to_original(),
                        entity_id=str(args.user_id),
                    ),
                )
                result = UserRoleMappingInputGroup(
                    user_role_input=user_role_mapping_input,
                    association_scopes_entities_input=associtation_input,
                )
    return result
