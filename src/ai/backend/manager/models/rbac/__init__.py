from __future__ import annotations

import enum
import uuid
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, Self, TypeVar, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload, with_loader_criteria

from .context import ClientContext
from .exceptions import InvalidScope
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


class ScopedUserRole(enum.StrEnum):
    OWNER = enum.auto()
    ADMIN = enum.auto()
    MONITOR = enum.auto()
    PRIVILEGED_MEMBER = enum.auto()  # User is part of a specific scope and has read(or some additional permissions) to objects that the scope has.
    MEMBER = (
        enum.auto()
    )  # User is part of a specific scope and has NO PERMISSION to objects that the scope has.


_EMPTY_FSET: frozenset = frozenset()


async def get_roles_in_scope(
    ctx: ClientContext,
    scope: BaseScope,
    db_session: AsyncSession | None = None,
) -> frozenset[ScopedUserRole]:
    from ..user import UserRole

    async def _calculate_role(db_session: AsyncSession) -> frozenset[ScopedUserRole]:
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
    ctx: ClientContext, db_session: AsyncSession, scope: BaseScope
) -> frozenset[ScopedUserRole]:
    from ..domain import DomainRow
    from ..group import GroupRow
    from ..user import UserRow

    match scope:
        case DomainScope(domain_name):
            stmt = (
                sa.select(DomainRow)
                .where(DomainRow.name == domain_name)
                .options(load_only(DomainRow.name))
            )
            domain_row = cast(DomainRow | None, await db_session.scalar(stmt))
            if domain_row is not None:
                return frozenset([ScopedUserRole.ADMIN])
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
                return frozenset([ScopedUserRole.ADMIN])
            else:
                return _EMPTY_FSET
        case UserScope(user_id):
            if ctx.user_id == user_id:
                return frozenset([ScopedUserRole.OWNER])
            stmt = (
                sa.select(UserRow).where(UserRow.uuid == user_id).options(load_only(UserRow.uuid))
            )
            user_row = cast(UserRow | None, await db_session.scalar(stmt))
            if user_row is not None:
                return frozenset([ScopedUserRole.ADMIN])
            else:
                return _EMPTY_FSET
        case _:
            raise InvalidScope(f"invalid scope `{scope}`")


async def _calculate_role_in_scope_for_monitor(
    ctx: ClientContext, db_session: AsyncSession, scope: BaseScope
) -> frozenset[ScopedUserRole]:
    from ..domain import DomainRow
    from ..group import AssocGroupUserRow, GroupRow
    from ..user import UserRow

    match scope:
        case DomainScope(domain_name):
            stmt = (
                sa.select(DomainRow)
                .where(DomainRow.name == domain_name)
                .options(load_only(DomainRow.name))
            )
            domain_row = cast(DomainRow | None, await db_session.scalar(stmt))
            if domain_row is not None:
                return frozenset([ScopedUserRole.MONITOR])
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
                result = frozenset([ScopedUserRole.ADMIN])
            else:
                return _EMPTY_FSET
            if project_row.users:
                result = frozenset([*result, ScopedUserRole.PRIVILEGED_MEMBER])
            return result
        case UserScope(user_id):
            if ctx.user_id == user_id:
                return frozenset([ScopedUserRole.OWNER])
            stmt = (
                sa.select(UserRow).where(UserRow.uuid == user_id).options(load_only(UserRow.uuid))
            )
            user_row = cast(UserRow | None, await db_session.scalar(stmt))
            if user_row is not None:
                return frozenset([ScopedUserRole.MONITOR])
            else:
                return _EMPTY_FSET
        case _:
            raise InvalidScope(f"invalid scope `{scope}`")


async def _calculate_role_in_scope_for_admin(
    ctx: ClientContext, db_session: AsyncSession, scope: BaseScope
) -> frozenset[ScopedUserRole]:
    from ..group import AssocGroupUserRow, GroupRow
    from ..user import UserRow

    match scope:
        case DomainScope(domain_name):
            if ctx.domain_name == domain_name:
                return frozenset([ScopedUserRole.ADMIN])
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
                result = frozenset([ScopedUserRole.ADMIN])
            else:
                return _EMPTY_FSET
            if project_row.users:
                result = frozenset([*result, ScopedUserRole.PRIVILEGED_MEMBER])
            return result
        case UserScope(user_id, domain_name):
            if ctx.user_id == user_id:
                return frozenset([ScopedUserRole.OWNER])
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
                return frozenset([ScopedUserRole.ADMIN])
            else:
                return _EMPTY_FSET
        case _:
            raise InvalidScope(f"invalid scope `{scope}`")


async def _calculate_role_in_scope_for_user(
    ctx: ClientContext, db_session: AsyncSession, scope: BaseScope
) -> frozenset[ScopedUserRole]:
    from ..group import AssocGroupUserRow

    match scope:
        case DomainScope(domain_name):
            if ctx.domain_name == domain_name:
                return frozenset([ScopedUserRole.MEMBER])
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
                return frozenset([ScopedUserRole.PRIVILEGED_MEMBER])
            else:
                return _EMPTY_FSET
        case UserScope(user_id):
            if ctx.user_id == user_id:
                return frozenset([ScopedUserRole.OWNER])
            else:
                return _EMPTY_FSET
        case _:
            raise InvalidScope(f"invalid scope `{scope}`")


class BaseScope(metaclass=ABCMeta):
    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass(frozen=True)
class DomainScope(BaseScope):
    domain_name: str

    def __str__(self) -> str:
        return f"Domain(name: {self.domain_name})"


@dataclass(frozen=True)
class ProjectScope(BaseScope):
    project_id: uuid.UUID
    domain_name: str | None = None

    def __str__(self) -> str:
        return f"Project(id: {self.project_id}, domain: {self.domain_name}])"


@dataclass(frozen=True)
class UserScope(BaseScope):
    user_id: uuid.UUID
    domain_name: str | None = None

    def __str__(self) -> str:
        return f"User(id: {self.user_id}, domain: {self.domain_name})"


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

    @classmethod
    def merge(cls, src: Self, trgt: Self) -> Self:
        def _merge_map(
            src: Mapping[Any, frozenset[PermissionType]],
            trgt: Mapping[Any, frozenset[PermissionType]],
        ) -> dict[Any, frozenset[PermissionType]]:
            val = {}
            for key in {*src.keys(), *trgt.keys()}:
                val[key] = src.get(key, frozenset()) | trgt.get(key, frozenset())
            return val

        return cls(
            _merge_map(src.user_id_to_permission_map, trgt.user_id_to_permission_map),
            _merge_map(src.project_id_to_permission_map, trgt.project_id_to_permission_map),
            _merge_map(src.domain_name_to_permission_map, trgt.domain_name_to_permission_map),
            _merge_map(
                src.object_id_to_additional_permission_map,
                trgt.object_id_to_additional_permission_map,
            ),
            _merge_map(
                src.object_id_to_overriding_permission_map,
                trgt.object_id_to_overriding_permission_map,
            ),
        )

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
    async def apply_customized_role(
        self,
        ctx: ClientContext,
        target_scope: BaseScope,
    ) -> frozenset[PermissionType]:
        # TODO: materialize customized roles
        raise NotImplementedError

    @classmethod
    async def calculate_permission_by_roles(
        cls,
        roles: Iterable[ScopedUserRole],
    ) -> frozenset[PermissionType]:
        result: frozenset[PermissionType] = frozenset()
        for role in roles:
            result |= await cls.calculate_permission_by_role(role)
        return result

    @classmethod
    async def calculate_permission_by_role(
        cls,
        role: ScopedUserRole,
    ) -> frozenset[PermissionType]:
        # This forces to implement a get_permission() method for each Built-in role.
        match role:
            case ScopedUserRole.OWNER:
                return await cls._permission_for_owner()
            case ScopedUserRole.ADMIN:
                return await cls._permission_for_admin()
            case ScopedUserRole.MONITOR:
                return await cls._permission_for_monitor()
            case ScopedUserRole.PRIVILEGED_MEMBER:
                return await cls._permission_for_privileged_member()
            case ScopedUserRole.MEMBER:
                return await cls._permission_for_member()

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
