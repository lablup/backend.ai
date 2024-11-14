from __future__ import annotations

import enum
import uuid
from abc import ABCMeta, abstractmethod
from collections.abc import Container, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, Self, TypeAlias, TypeVar, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload, with_loader_criteria

from .context import ClientContext
from .exceptions import InvalidScope, ScopeTypeMismatch
from .permission_defs import BasePermission

__all__: Sequence[str] = (
    "DomainScope",
    "ProjectScope",
    "UserScope",
    "StorageHost",
    "ImageRegistry",
    "ScalingGroup",
    "AbstractPermissionContext",
    "AbstractPermissionContextBuilder",
)


PermissionType = TypeVar("PermissionType", bound=BasePermission)


class PredefinedRole(enum.StrEnum):
    OWNER = enum.auto()
    ADMIN = enum.auto()
    MONITOR = enum.auto()
    # Privileged member is a user who is part of a specific scope
    # and has read(or some additional permissions) to objects that the scope has.
    # e.g. Project member
    PRIVILEGED_MEMBER = enum.auto()
    # Member is a user who is part of a specific scope
    # and has NO PERMISSION to objects that the scope has.
    # e.g. Domain member
    MEMBER = enum.auto()


_EMPTY_FSET: frozenset = frozenset()


async def get_predefined_roles_in_scope(
    ctx: ClientContext,
    scope: ScopeType,
    db_session: AsyncSession | None = None,
) -> frozenset[PredefinedRole]:
    from ..user import UserRole

    async def _calculate_role(db_session: AsyncSession) -> frozenset[PredefinedRole]:
        match ctx.user_role:
            case UserRole.SUPERADMIN:
                return await _calculate_role_in_scope_for_suadmin(ctx, db_session, scope)
            case UserRole.MONITOR:
                return await _calculate_role_in_scope_for_monitor(ctx, db_session, scope)
            case UserRole.ADMIN:
                return await _calculate_role_in_scope_for_admin(ctx, db_session, scope)
            case UserRole.USER:
                return await _calculate_role_in_scope_for_user(ctx, db_session, scope)

    if db_session is None:
        async with ctx.db.begin_readonly_session() as _db_session:
            return await _calculate_role(_db_session)
    else:
        return await _calculate_role(db_session)


async def _calculate_role_in_scope_for_suadmin(
    ctx: ClientContext, db_session: AsyncSession, scope: ScopeType
) -> frozenset[PredefinedRole]:
    from ..domain import DomainRow
    from ..group import GroupRow
    from ..user import UserRow

    match scope:
        case SystemScope():
            return frozenset([PredefinedRole.ADMIN])
        case DomainScope(domain_name):
            stmt = (
                sa.select(DomainRow)
                .where(DomainRow.name == domain_name)
                .options(load_only(DomainRow.name))
            )
            domain_row = cast(DomainRow | None, await db_session.scalar(stmt))
            if domain_row is not None:
                return frozenset([PredefinedRole.ADMIN])
            else:
                return _EMPTY_FSET
        case ProjectScope(project_id):
            stmt = (
                sa.select(GroupRow).where(GroupRow.id == project_id).options(load_only(GroupRow.id))
            )
            project_row = cast(GroupRow | None, await db_session.scalar(stmt))
            if project_row is None:
                return _EMPTY_FSET
            if project_row is not None:
                return frozenset([PredefinedRole.ADMIN])
            else:
                return _EMPTY_FSET
        case UserScope(user_id):
            if ctx.user_id == user_id:
                return frozenset([PredefinedRole.OWNER])
            stmt = (
                sa.select(UserRow).where(UserRow.uuid == user_id).options(load_only(UserRow.uuid))
            )
            user_row = cast(UserRow | None, await db_session.scalar(stmt))
            if user_row is not None:
                return frozenset([PredefinedRole.ADMIN])
            else:
                return _EMPTY_FSET


async def _calculate_role_in_scope_for_monitor(
    ctx: ClientContext, db_session: AsyncSession, scope: ScopeType
) -> frozenset[PredefinedRole]:
    from ..domain import DomainRow
    from ..group import AssocGroupUserRow, GroupRow
    from ..user import UserRow

    match scope:
        case SystemScope():
            return frozenset([PredefinedRole.MONITOR])
        case DomainScope(domain_name):
            stmt = (
                sa.select(DomainRow)
                .where(DomainRow.name == domain_name)
                .options(load_only(DomainRow.name))
            )
            domain_row = cast(DomainRow | None, await db_session.scalar(stmt))
            if domain_row is not None:
                return frozenset([PredefinedRole.MONITOR])
            else:
                return _EMPTY_FSET
        case ProjectScope(project_id):
            stmt = (
                sa.select(GroupRow)
                .where(GroupRow.id == project_id)
                .options(
                    load_only(GroupRow.id, GroupRow.domain_name),
                    selectinload(GroupRow.users),
                    with_loader_criteria(
                        AssocGroupUserRow, AssocGroupUserRow.user_id == ctx.user_id
                    ),
                )
            )
            project_row = cast(GroupRow | None, await db_session.scalar(stmt))
            if project_row is None:
                return _EMPTY_FSET
            if project_row.domain_name == ctx.domain_name:
                result = frozenset([PredefinedRole.ADMIN])
            else:
                return _EMPTY_FSET
            if project_row.users:
                result = frozenset([*result, PredefinedRole.PRIVILEGED_MEMBER])
            return result
        case UserScope(user_id):
            if ctx.user_id == user_id:
                return frozenset([PredefinedRole.OWNER])
            stmt = (
                sa.select(UserRow).where(UserRow.uuid == user_id).options(load_only(UserRow.uuid))
            )
            user_row = cast(UserRow | None, await db_session.scalar(stmt))
            if user_row is not None:
                return frozenset([PredefinedRole.MONITOR])
            else:
                return _EMPTY_FSET


async def _calculate_role_in_scope_for_admin(
    ctx: ClientContext, db_session: AsyncSession, scope: ScopeType
) -> frozenset[PredefinedRole]:
    from ..group import AssocGroupUserRow, GroupRow
    from ..user import UserRow

    match scope:
        case SystemScope():
            return _EMPTY_FSET
        case DomainScope(domain_name):
            if ctx.domain_name == domain_name:
                return frozenset([PredefinedRole.ADMIN])
            else:
                return _EMPTY_FSET
        case ProjectScope(project_id):
            stmt = (
                sa.select(GroupRow)
                .where(GroupRow.id == project_id)
                .options(
                    load_only(GroupRow.id, GroupRow.domain_name),
                    selectinload(GroupRow.users),
                    with_loader_criteria(
                        AssocGroupUserRow, AssocGroupUserRow.user_id == ctx.user_id
                    ),
                )
            )
            project_row = cast(GroupRow | None, await db_session.scalar(stmt))
            if project_row is None:
                return _EMPTY_FSET

            if project_row.domain_name == ctx.domain_name:
                result = frozenset([PredefinedRole.ADMIN])
            else:
                return _EMPTY_FSET
            if project_row.users:
                result = frozenset([*result, PredefinedRole.PRIVILEGED_MEMBER])
            return result
        case UserScope(user_id, domain_name):
            if ctx.user_id == user_id:
                return frozenset([PredefinedRole.OWNER])
            if domain_name is not None:
                _domain_name = domain_name
            else:
                stmt = (
                    sa.select(UserRow)
                    .where(UserRow.uuid == user_id)
                    .options(load_only(UserRow.domain_name))
                )
                user_row = cast(UserRow | None, await db_session.scalar(stmt))
                if user_row is None:
                    return _EMPTY_FSET
                _domain_name = user_row.domain_name
            if _domain_name == ctx.domain_name:
                return frozenset([PredefinedRole.ADMIN])
            else:
                return _EMPTY_FSET


async def _calculate_role_in_scope_for_user(
    ctx: ClientContext, db_session: AsyncSession, scope: ScopeType
) -> frozenset[PredefinedRole]:
    from ..group import AssocGroupUserRow

    match scope:
        case SystemScope():
            return _EMPTY_FSET
        case DomainScope(domain_name):
            if ctx.domain_name == domain_name:
                return frozenset([PredefinedRole.MEMBER])
            else:
                return _EMPTY_FSET
        case ProjectScope(project_id):
            stmt = (
                sa.select(AssocGroupUserRow)
                .where(
                    (AssocGroupUserRow.user_id == ctx.user_id)
                    & (AssocGroupUserRow.group_id == project_id)
                )
                .options(load_only(AssocGroupUserRow.user_id))
            )
            assoc_row = cast(AssocGroupUserRow | None, await db_session.scalar(stmt))
            if assoc_row is not None:
                return frozenset([PredefinedRole.PRIVILEGED_MEMBER])
            else:
                return _EMPTY_FSET
        case UserScope(user_id):
            if ctx.user_id == user_id:
                return frozenset([PredefinedRole.OWNER])
            else:
                return _EMPTY_FSET


class BaseScope(metaclass=ABCMeta):
    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def serialize(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, val: str) -> Self:
        pass


@dataclass(frozen=True)
class SystemScope(BaseScope):
    def __str__(self) -> str:
        return "system scope()"

    def serialize(self) -> str:
        return "system:"

    @classmethod
    def deserialize(cls, val: str) -> Self:
        type_, _, _ = val.partition(":")
        if type_ != "system":
            raise ScopeTypeMismatch
        return cls()


@dataclass(frozen=True)
class DomainScope(BaseScope):
    domain_name: str

    def __str__(self) -> str:
        return f"Domain(name: {self.domain_name})"

    def serialize(self) -> str:
        return f"domain:{self.domain_name}"

    @classmethod
    def deserialize(cls, val: str) -> Self:
        type_, _, domain_name = val.partition(":")
        if type_ != "domain":
            raise ScopeTypeMismatch
        return cls(domain_name)


@dataclass(frozen=True)
class ProjectScope(BaseScope):
    project_id: uuid.UUID
    domain_name: str | None = None

    def __str__(self) -> str:
        return f"Project(id: {self.project_id}, domain: {self.domain_name}])"

    def serialize(self) -> str:
        if self.domain_name is not None:
            return f"project:{self.project_id}:{self.domain_name}"
        else:
            return f"project:{self.project_id}"

    @classmethod
    def deserialize(cls, val: str) -> Self:
        type_, _, values = val.partition(":")
        if type_ != "project":
            raise ScopeTypeMismatch
        raw_project_id, _, domain_name = values.partition(":")
        if domain_name:
            return cls(uuid.UUID(raw_project_id), domain_name)
        else:
            return cls(uuid.UUID(raw_project_id))


@dataclass(frozen=True)
class UserScope(BaseScope):
    user_id: uuid.UUID
    domain_name: str | None = None

    def __str__(self) -> str:
        return f"User(id: {self.user_id}, domain: {self.domain_name})"

    def serialize(self) -> str:
        if self.domain_name is not None:
            return f"user:{self.user_id}:{self.domain_name}"
        else:
            return f"user:{self.user_id}"

    @classmethod
    def deserialize(cls, val: str) -> Self:
        type_, _, values = val.partition(":")
        if type_ != "user":
            raise ScopeTypeMismatch
        raw_user_id, _, domain_name = values.partition(":")
        if domain_name:
            return cls(uuid.UUID(raw_user_id), domain_name)
        else:
            return cls(uuid.UUID(raw_user_id))


ScopeType: TypeAlias = SystemScope | DomainScope | ProjectScope | UserScope


def deserialize_scope(val: str) -> ScopeType:
    """
    Deserialize a string value in the format '<SCOPE_TYPE>:<SCOPE_ID>'.

    This function takes a string input representing a scope and deserializes it into `Scope` object
    containing the scope type, scope ID (if applicable), and an optional additional scope ID.

    The input should adhere to one of the following formats:
    1. '<SCOPE_TYPE>' (for system scope)
    2. '<SCOPE_TYPE>:<SCOPE_ID>'

    Scope types and their corresponding ID formats:
    - system: No ID (covers the whole system)
    - domain: String ID
    - project: UUID
    - user: UUID

    Args:
        value (str): The input string to deserialize, in one of the specified formats.

    Returns:
        One of [SystemScope, DomainScope, ProjectScope, UserScope] object.

    Raises:
        rbac.exceptions.InvalidScope:
            If the input string does not conform to the expected formats or if the scope type is invalid.
        ValueError:
            If the scope ID format doesn't match the expected type for the given scope.

    Examples:
        >>> deserialize_scope("system")
        SystemScope()
        >>> deserialize_scope("domain:default")
        DomainScope("default")
        >>> deserialize_scope("project:123e4567-e89b-12d3-a456-426614174000")
        ProjectScope(UUID('123e4567-e89b-12d3-a456-426614174000'))
        >>> deserialize_scope("user:123e4567-e89b-12d3-a456-426614174000")
        UserScope(UUID('123e4567-e89b-12d3-a456-426614174000'))
    """
    for scope in (SystemScope, DomainScope, ProjectScope, UserScope):
        try:
            return scope.deserialize(val)
        except ScopeTypeMismatch:
            continue
    else:
        raise InvalidScope(f"Invalid scope (s: {scope})")


# Extra scope is to address some scopes that contain specific object types
# such as registries for images, scaling groups for agents, storage hosts for vfolders etc.
class ExtraScope:
    pass


@dataclass(frozen=True)
class StorageHost(ExtraScope):
    name: str


@dataclass(frozen=True)
class ImageRegistry(ExtraScope):
    name: str


@dataclass(frozen=True)
class ScalingGroup(ExtraScope):
    name: str


ObjectType = TypeVar("ObjectType")
ObjectIDType = TypeVar("ObjectIDType")


@dataclass
class AbstractPermissionContext(
    Generic[PermissionType, ObjectType, ObjectIDType], metaclass=ABCMeta
):
    """
    Define permissions under given User, Project or Domain scopes.
    Each field of this class represents a mapping of ["accessible scope id", "permissions under the scope"].
    For example, `project` field has a mapping of ["accessible project id", "permissions under the project"].
    {
        "PROJECT_A_ID": {"READ", "WRITE", "DELETE"}
        "PROJECT_B_ID": {"READ"}
    }

    `additional` and `overriding` fields have a mapping of ["object id", "permissions applied to the object"].
    `additional` field is used to add permissions to specific objects. It can be used for admins.
    `overriding` field is used to address exceptional cases such as permission overriding or cover other scopes(scaling groups or storage hosts etc).
    """

    user_id_to_permission_map: Mapping[uuid.UUID, frozenset[PermissionType]] = field(
        default_factory=dict
    )
    project_id_to_permission_map: Mapping[uuid.UUID, frozenset[PermissionType]] = field(
        default_factory=dict
    )
    domain_name_to_permission_map: Mapping[str, frozenset[PermissionType]] = field(
        default_factory=dict
    )

    object_id_to_additional_permission_map: Mapping[ObjectIDType, frozenset[PermissionType]] = (
        field(default_factory=dict)
    )
    object_id_to_overriding_permission_map: Mapping[ObjectIDType, frozenset[PermissionType]] = (
        field(default_factory=dict)
    )

    def filter_by_permission(self, permission_to_include: PermissionType) -> None:
        self.user_id_to_permission_map = {
            uid: permissions
            for uid, permissions in self.user_id_to_permission_map.items()
            if permission_to_include in permissions
        }
        self.project_id_to_permission_map = {
            pid: permissions
            for pid, permissions in self.project_id_to_permission_map.items()
            if permission_to_include in permissions
        }
        self.domain_name_to_permission_map = {
            dname: permissions
            for dname, permissions in self.domain_name_to_permission_map.items()
            if permission_to_include in permissions
        }
        self.object_id_to_additional_permission_map = {
            obj_id: permissions
            for obj_id, permissions in self.object_id_to_additional_permission_map.items()
            if permission_to_include in permissions
        }
        self.object_id_to_overriding_permission_map = {
            obj_id: permissions
            for obj_id, permissions in self.object_id_to_overriding_permission_map.items()
            if permission_to_include in permissions
        }

    def merge(self, trgt: Self) -> None:
        def _merge_map(
            src: Mapping[Any, frozenset[PermissionType]],
            trgt: Mapping[Any, frozenset[PermissionType]],
        ) -> dict[Any, frozenset[PermissionType]]:
            val = {}
            for key in {*src.keys(), *trgt.keys()}:
                val[key] = src.get(key, frozenset()) | trgt.get(key, frozenset())
            return val

        self.user_id_to_permission_map = _merge_map(
            self.user_id_to_permission_map, trgt.user_id_to_permission_map
        )
        self.project_id_to_permission_map = _merge_map(
            self.project_id_to_permission_map, trgt.project_id_to_permission_map
        )
        self.domain_name_to_permission_map = _merge_map(
            self.domain_name_to_permission_map, trgt.domain_name_to_permission_map
        )
        self.object_id_to_additional_permission_map = _merge_map(
            self.object_id_to_additional_permission_map, trgt.object_id_to_additional_permission_map
        )
        self.object_id_to_overriding_permission_map = _merge_map(
            self.object_id_to_overriding_permission_map, trgt.object_id_to_overriding_permission_map
        )

    def __add__(self, other: Self) -> Self:
        self.merge(other)
        return self

    @abstractmethod
    async def build_query(self) -> sa.sql.Select | None:
        pass

    @abstractmethod
    async def calculate_final_permission(self, rbac_obj: ObjectType) -> frozenset[PermissionType]:
        """
        Calculate the final permissions applied to the given object based on the fields in this class.
        """
        pass


PermissionContextType = TypeVar("PermissionContextType", bound=AbstractPermissionContext)


class AbstractPermissionContextBuilder(
    Generic[PermissionType, PermissionContextType], metaclass=ABCMeta
):
    @abstractmethod
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[PermissionType]:
        pass

    @classmethod
    async def _calculate_permission_by_predefined_roles(
        cls,
        roles: Iterable[PredefinedRole],
    ) -> frozenset[PermissionType]:
        result: frozenset[PermissionType] = frozenset()
        for role in roles:
            result |= await cls._calculate_permission_by_role(role)
        return result

    @classmethod
    async def _calculate_permission_by_role(
        cls,
        role: PredefinedRole,
    ) -> frozenset[PermissionType]:
        # This forces to implement a get_permission() method for each Built-in role.
        match role:
            case PredefinedRole.OWNER:
                return await cls._permission_for_owner()
            case PredefinedRole.ADMIN:
                return await cls._permission_for_admin()
            case PredefinedRole.MONITOR:
                return await cls._permission_for_monitor()
            case PredefinedRole.PRIVILEGED_MEMBER:
                return await cls._permission_for_privileged_member()
            case PredefinedRole.MEMBER:
                return await cls._permission_for_member()

    async def build(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
        requested_permission: PermissionType,
    ) -> PermissionContextType:
        match target_scope:
            case SystemScope():
                permission_ctx = await self.build_ctx_in_system_scope(ctx)
            case DomainScope():
                permission_ctx = await self.build_ctx_in_domain_scope(ctx, target_scope)
            case ProjectScope():
                permission_ctx = await self.build_ctx_in_project_scope(ctx, target_scope)
            case UserScope():
                permission_ctx = await self.build_ctx_in_user_scope(ctx, target_scope)
        permission_ctx.filter_by_permission(requested_permission)
        return permission_ctx

    @abstractmethod
    async def build_ctx_in_system_scope(self, ctx: ClientContext) -> PermissionContextType:
        pass

    @abstractmethod
    async def build_ctx_in_domain_scope(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> PermissionContextType:
        pass

    @abstractmethod
    async def build_ctx_in_project_scope(
        self, ctx: ClientContext, scope: ProjectScope
    ) -> PermissionContextType:
        pass

    @abstractmethod
    async def build_ctx_in_user_scope(
        self, ctx: ClientContext, scope: UserScope
    ) -> PermissionContextType:
        pass

    @classmethod
    @abstractmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[PermissionType]:
        pass

    @classmethod
    @abstractmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[PermissionType]:
        pass

    @classmethod
    @abstractmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[PermissionType]:
        pass

    @classmethod
    @abstractmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[PermissionType]:
        pass

    @classmethod
    @abstractmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[PermissionType]:
        pass


class RBACModel(Generic[PermissionType]):
    @property
    @abstractmethod
    def permissions(self) -> Container[PermissionType]:
        pass


T_RBACModel = TypeVar("T_RBACModel", bound=RBACModel)
T_PropertyReturn = TypeVar("T_PropertyReturn")


def required_permission(permission: PermissionType):
    def wrapper(
        property_func: Callable[[T_RBACModel], T_PropertyReturn],
    ) -> Callable[[T_RBACModel], Optional[T_PropertyReturn]]:
        def wrapped(self: T_RBACModel) -> Optional[T_PropertyReturn]:
            if permission in self.permissions:
                return property_func(self)
            else:
                return None

        return wrapped

    return wrapper
