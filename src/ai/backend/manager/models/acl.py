from __future__ import annotations

import enum
import uuid
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, List, Sequence, TypeVar

import graphene
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from ai.backend.common.types import VFolderHostPermission

from .group import AssocGroupUserRow, GroupRow, UserRoleInProject
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext


__all__: Sequence[str] = (
    "PredefinedAtomicPermission",
    "get_all_permissions",
)


class BaseACLPermission(enum.StrEnum):
    pass


ACLPermissionType = TypeVar("ACLPermissionType", bound=BaseACLPermission)


@dataclass
class ClientContext:
    db_conn: AsyncConnection

    domain_name: str
    user_id: uuid.UUID
    user_role: UserRole

    _project_ctx: Mapping[uuid.UUID, UserRoleInProject] | None = None

    async def get_or_init_project_ctx(self) -> Mapping[uuid.UUID, UserRoleInProject]:
        if self._project_ctx is None:
            match self.user_role:
                case UserRole.SUPERADMIN | UserRole.MONITOR:
                    stmt = sa.select(GroupRow)
                    async with AsyncSession(self.db_conn) as db_session:
                        self._project_ctx = {
                            row.id: UserRoleInProject.ADMIN
                            for row in await db_session.scalars(stmt)
                        }
                case UserRole.ADMIN:
                    stmt = sa.select(GroupRow).where(GroupRow.domain_name == self.domain_name)
                    async with AsyncSession(self.db_conn) as db_session:
                        self._project_ctx = {
                            row.id: UserRoleInProject.ADMIN
                            for row in await db_session.scalars(stmt)
                        }
                case UserRole.USER:
                    stmt = (
                        sa.select(AssocGroupUserRow)
                        .select_from(sa.join(AssocGroupUserRow, GroupRow))
                        .where(
                            (AssocGroupUserRow.user_id == self.user_id)
                            & (GroupRow.domain_name == self.domain_name)
                        )
                    )
                    async with AsyncSession(self.db_conn) as db_session:
                        self._project_ctx = {
                            row.group_id: UserRoleInProject.USER
                            for row in await db_session.scalars(stmt)
                        }
        return self._project_ctx


class BaseACLScope:
    pass


@dataclass(frozen=True)
class DomainScope(BaseACLScope):
    domain_name: str


@dataclass(frozen=True)
class ProjectScope(BaseACLScope):
    project_id: uuid.UUID


@dataclass(frozen=True)
class UserScope(BaseACLScope):
    user_id: uuid.UUID


# Extra ACL scope is to address some scopes that contain specific object types
# such as registries for images, scaling groups for agents, storage hosts for vfolders etc.
class ExtraACLScope:
    pass


@dataclass(frozen=True)
class StorageHost(ExtraACLScope):
    name: str


@dataclass(frozen=True)
class ImageRegistry(ExtraACLScope):
    name: str


@dataclass(frozen=True)
class ScalingGroup(ExtraACLScope):
    name: str


@dataclass(frozen=True)
class ACLObjectScope:
    base_scope: BaseACLScope
    extra_scopes: list[ExtraACLScope] = field(default_factory=list)


ACLObjectType = TypeVar("ACLObjectType")
ACLObjectIDType = TypeVar("ACLObjectIDType")


@dataclass
class AbstractACLPermissionContext(
    Generic[ACLPermissionType, ACLObjectType, ACLObjectIDType], metaclass=ABCMeta
):
    """
    Define ACL permissions under given User, Project or Domain scopes.
    Each field of this class represents a mapping of ["accessible scope id", "permissions under the scope"].
    For example, `project` field has a mapping of ["accessible project id", "permissions under the project"].
    {
        "PROJECT_A_ID": {"READ", "WRITE", "DELETE"}
        "PROJECT_B_ID": {"READ"}
    }

    `additional` and `overridden` fields have a mapping of ["ACL object id", "permissions applied to the object"].
    `additional` field is used to add permissions to specific ACL objects. It can be used for admins.
    `overridden` field is used to address exceptional cases such as permission overriding or cover other scopes(scaling groups or storage hosts etc).
    """

    user_id_to_permission_map: Mapping[uuid.UUID, frozenset[ACLPermissionType]] = field(
        default_factory=dict
    )
    project_id_to_permission_map: Mapping[uuid.UUID, frozenset[ACLPermissionType]] = field(
        default_factory=dict
    )
    domain_name_to_permission_map: Mapping[str, frozenset[ACLPermissionType]] = field(
        default_factory=dict
    )

    object_id_to_additional_permission_map: Mapping[
        ACLObjectIDType, frozenset[ACLPermissionType]
    ] = field(default_factory=dict)
    object_id_to_overriding_permission_map: Mapping[
        ACLObjectIDType, frozenset[ACLPermissionType]
    ] = field(default_factory=dict)

    def filter_by_permission(self, permission_to_include: ACLPermissionType) -> None:
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
    async def determine_permission(self, acl_obj: ACLObjectType) -> frozenset[ACLPermissionType]:
        """
        Determine permissions applied to the given ACL object based on the fields in this class.
        """
        pass


ACLPermissionContextType = TypeVar("ACLPermissionContextType", bound=AbstractACLPermissionContext)


class AbstractACLPermissionContextBuilder(
    Generic[ACLPermissionType, ACLPermissionContextType], metaclass=ABCMeta
):
    @classmethod
    async def build(
        cls,
        db_session: AsyncSession,
        ctx: ClientContext,
        target_scope: ACLObjectScope,
        *,
        permission: ACLPermissionType | None = None,
    ) -> ACLPermissionContextType:
        match target_scope.base_scope:
            case UserScope(user_id=user_id):
                result = await cls._build_in_user_scope(
                    db_session, ctx, user_id, extra_target_scopes=target_scope.extra_scopes
                )
            case ProjectScope(project_id=project_id):
                result = await cls._build_in_project_scope(
                    db_session, ctx, project_id, extra_target_scopes=target_scope.extra_scopes
                )
            case DomainScope(domain_name=domain_name):
                result = await cls._build_in_domain_scope(
                    db_session, ctx, domain_name, extra_target_scopes=target_scope.extra_scopes
                )
            case _:
                raise RuntimeError(f"invalid ACL scope `{target_scope}`")
        if permission is not None:
            result.filter_by_permission(permission)
        return result

    @classmethod
    @abstractmethod
    async def _build_in_user_scope(
        cls,
        db_session: AsyncSession,
        ctx: ClientContext,
        user_id: uuid.UUID,
        *,
        extra_target_scopes: Iterable[ExtraACLScope],
    ) -> ACLPermissionContextType:
        pass

    @classmethod
    @abstractmethod
    async def _build_in_project_scope(
        cls,
        db_session: AsyncSession,
        ctx: ClientContext,
        project_id: uuid.UUID,
        *,
        extra_target_scopes: Iterable[ExtraACLScope],
    ) -> ACLPermissionContextType:
        pass

    @classmethod
    @abstractmethod
    async def _build_in_domain_scope(
        cls,
        db_session: AsyncSession,
        ctx: ClientContext,
        domain_name: str,
        *,
        extra_target_scopes: Iterable[ExtraACLScope],
    ) -> ACLPermissionContextType:
        pass


def get_all_vfolder_host_permissions() -> List[str]:
    return [perm.value for perm in VFolderHostPermission]


def get_all_permissions() -> Mapping[str, Any]:
    return {
        "vfolder_host_permission_list": get_all_vfolder_host_permissions(),
    }


class PredefinedAtomicPermission(graphene.ObjectType):
    vfolder_host_permission_list = graphene.List(lambda: graphene.String)

    async def resolve_vfolder_host_permission_list(self, info: graphene.ResolveInfo) -> List[str]:
        return get_all_vfolder_host_permissions()

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
    ) -> PredefinedAtomicPermission:
        return cls(**get_all_permissions())
