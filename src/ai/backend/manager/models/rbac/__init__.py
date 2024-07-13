from __future__ import annotations

import enum
import uuid
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, Sequence, TypeVar

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from ..group import AssocGroupUserRow, GroupRow, UserRoleInProject
from ..user import UserRole

if TYPE_CHECKING:
    from ..utils import ExtendedAsyncSAEngine


__all__: Sequence[str] = (
    "BasePermission",
    "ClientContext",
    "DomainScope",
    "ProjectScope",
    "UserScope",
    "StorageHost",
    "ImageRegistry",
    "ScalingGroup",
    "AbstractPermissionContext",
    "AbstractPermissionContextBuilder",
)


class BasePermission(enum.StrEnum):
    pass


PermissionType = TypeVar("PermissionType", bound=BasePermission)


ProjectContext = Mapping[uuid.UUID, UserRoleInProject]


@dataclass
class ClientContext:
    db: ExtendedAsyncSAEngine

    domain_name: str
    user_id: uuid.UUID
    user_role: UserRole

    _domain_project_ctx: Mapping[str, ProjectContext] | None = field(init=False, default=None)

    async def get_accessible_projects_in_domain(
        self, db_session: AsyncSession, domain_name: str
    ) -> ProjectContext | None:
        match self.user_role:
            case UserRole.SUPERADMIN | UserRole.MONITOR:
                if self._domain_project_ctx is None:
                    self._domain_project_ctx = {}
                if domain_name not in self._domain_project_ctx:
                    stmt = (
                        sa.select(GroupRow)
                        .where(GroupRow.domain_name == domain_name)
                        .options(load_only(GroupRow.id))
                    )
                    self._domain_project_ctx = {
                        **self._domain_project_ctx,
                        domain_name: {
                            row.id: UserRoleInProject.ADMIN
                            for row in await db_session.scalars(stmt)
                        },
                    }
            case UserRole.ADMIN | UserRole.USER:
                _project_ctx = await self._get_or_init_project_ctx(db_session)
                self._domain_project_ctx = {self.domain_name: _project_ctx}
        return self._domain_project_ctx.get(domain_name)

    async def get_user_role_in_project(
        self, db_session: AsyncSession, project_id: uuid.UUID
    ) -> UserRoleInProject:
        match self.user_role:
            case UserRole.SUPERADMIN | UserRole.MONITOR:
                return UserRoleInProject.ADMIN
            case UserRole.ADMIN | UserRole.USER:
                _project_ctx = await self._get_or_init_project_ctx(db_session)
                return _project_ctx.get(project_id, UserRoleInProject.NONE)

    async def _get_or_init_project_ctx(self, db_session: AsyncSession) -> ProjectContext:
        match self.user_role:
            case UserRole.SUPERADMIN | UserRole.MONITOR:
                # Superadmins and monitors can access to ALL projects in the system.
                # Let's not fetch all project data from DB.
                return {}
            case UserRole.ADMIN:
                if (
                    self._domain_project_ctx is None
                    or self.domain_name not in self._domain_project_ctx
                ):
                    stmt = (
                        sa.select(GroupRow)
                        .where(GroupRow.domain_name == self.domain_name)
                        .options(load_only(GroupRow.id))
                    )
                    _project_ctx = {
                        row.id: UserRoleInProject.ADMIN for row in await db_session.scalars(stmt)
                    }
                    self._domain_project_ctx = {self.domain_name: _project_ctx}
                return self._domain_project_ctx[self.domain_name]
            case UserRole.USER:
                if (
                    self._domain_project_ctx is None
                    or self.domain_name not in self._domain_project_ctx
                ):
                    stmt = (
                        sa.select(AssocGroupUserRow)
                        .select_from(sa.join(AssocGroupUserRow, GroupRow))
                        .where(
                            (AssocGroupUserRow.user_id == self.user_id)
                            & (GroupRow.domain_name == self.domain_name)
                        )
                    )
                    _project_ctx = {
                        row.id: UserRoleInProject.USER for row in await db_session.scalars(stmt)
                    }
                    self._domain_project_ctx = {self.domain_name: _project_ctx}
                return self._domain_project_ctx[self.domain_name]


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

    def __str__(self) -> str:
        return f"Project(id: {self.project_id})"


@dataclass(frozen=True)
class UserScope(BaseScope):
    user_id: uuid.UUID

    def __str__(self) -> str:
        return f"User(id: {self.user_id})"


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

    @abstractmethod
    async def build_query(self) -> sa.sql.Select | None:
        pass

    @abstractmethod
    async def calculate_final_permission(self, acl_obj: ObjectType) -> frozenset[PermissionType]:
        """
        Calculate the final permissions applied to the given  object based on the fields in this class.
        """
        pass


PermissionContextType = TypeVar("PermissionContextType", bound=AbstractPermissionContext)


class AbstractPermissionContextBuilder(
    Generic[PermissionType, PermissionContextType], metaclass=ABCMeta
):
    async def build(
        self,
        ctx: ClientContext,
        target_scope: BaseScope,
        *,
        permission: PermissionType | None = None,
    ) -> PermissionContextType:
        match target_scope:
            case UserScope(user_id=user_id):
                result = await self._build_in_user_scope(ctx, user_id)
            case ProjectScope(project_id=project_id):
                result = await self._build_in_project_scope(ctx, project_id)
            case DomainScope(domain_name=domain_name):
                result = await self._build_in_domain_scope(ctx, domain_name)
            case _:
                raise RuntimeError(f"invalid scope `{target_scope}`")
        if permission is not None:
            result.filter_by_permission(permission)
        return result

    @abstractmethod
    async def _build_in_user_scope(
        self,
        ctx: ClientContext,
        user_id: uuid.UUID,
    ) -> PermissionContextType:
        pass

    @abstractmethod
    async def _build_in_project_scope(
        self,
        ctx: ClientContext,
        project_id: uuid.UUID,
    ) -> PermissionContextType:
        pass

    @abstractmethod
    async def _build_in_domain_scope(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> PermissionContextType:
        pass
