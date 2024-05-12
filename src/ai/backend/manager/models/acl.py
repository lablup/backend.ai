from __future__ import annotations

import enum
import uuid
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
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


class AbstractACLPermission(enum.StrEnum):
    pass


ACLPermissionType = TypeVar("ACLPermissionType", bound=AbstractACLPermission)


@dataclass
class RequesterContext:
    db_conn: AsyncConnection

    domain_name: str
    user_id: uuid.UUID
    user_role: UserRole

    project_ctx: Mapping[uuid.UUID, UserRoleInProject] | None = None

    async def get_or_init_project_ctx(self) -> Mapping[uuid.UUID, UserRoleInProject]:
        if self.project_ctx is None:
            if self.user_role in (UserRole.SUPERADMIN, UserRole.ADMIN):
                role_in_project = UserRoleInProject.ADMIN
            else:
                role_in_project = UserRoleInProject.USER
            stmt = (
                sa.select(AssocGroupUserRow)
                .select_from(sa.join(AssocGroupUserRow, GroupRow))
                .where(
                    (AssocGroupUserRow.user_id == self.user_id)
                    & (GroupRow.domain_name == self.domain_name)
                )
            )
            async with AsyncSession(self.db_conn) as db_session:
                self.project_ctx = {
                    row.group_id: role_in_project for row in await db_session.scalars(stmt)
                }
        return self.project_ctx


class RequestedScope:
    pass


@dataclass(frozen=True)
class RequestedDomainScope(RequestedScope):
    domain_name: str


@dataclass(frozen=True)
class RequestedProjectScope(RequestedScope):
    project_id: uuid.UUID


@dataclass(frozen=True)
class RequestedUserScope(RequestedScope):
    user_id: uuid.UUID


ACLObjectType = TypeVar("ACLObjectType")


@dataclass
class AbstractScopePermissionMap(Generic[ACLPermissionType, ACLObjectType], metaclass=ABCMeta):
    user: Mapping[uuid.UUID, frozenset[ACLPermissionType]]
    project: Mapping[uuid.UUID, frozenset[ACLPermissionType]]
    domain: Mapping[str, frozenset[ACLPermissionType]]

    @abstractmethod
    async def determine_permission(self, acl_obj: ACLObjectType) -> frozenset[ACLPermissionType]:
        pass


ScopePermissionMapType = TypeVar("ScopePermissionMapType", bound=AbstractScopePermissionMap)


class AbstractScopePermissionMapBuilder(Generic[ScopePermissionMapType], metaclass=ABCMeta):
    @classmethod
    async def build(
        cls,
        db_session: AsyncSession,
        ctx: RequesterContext,
        requested_scope: RequestedScope,
    ) -> ScopePermissionMapType:
        match requested_scope:
            case RequestedUserScope(user_id=user_id):
                return await cls._build_in_user_scope(db_session, ctx, user_id)
            case RequestedProjectScope(project_id=project_id):
                return await cls._build_in_project_scope(db_session, ctx, project_id)
            case RequestedDomainScope(domain_name=domain_name):
                return await cls._build_in_domain_scope(db_session, ctx, domain_name)
            case _:
                pass
        raise RuntimeError(f"invalid request scope {requested_scope}")

    @classmethod
    @abstractmethod
    async def _build_in_user_scope(
        cls,
        db_session: AsyncSession,
        ctx: RequesterContext,
        user_id: uuid.UUID,
    ) -> ScopePermissionMapType:
        pass

    @classmethod
    @abstractmethod
    async def _build_in_project_scope(
        cls,
        db_session: AsyncSession,
        ctx: RequesterContext,
        project_id: uuid.UUID,
    ) -> ScopePermissionMapType:
        pass

    @classmethod
    @abstractmethod
    async def _build_in_domain_scope(
        cls,
        db_session: AsyncSession,
        ctx: RequesterContext,
        domain_name: str,
    ) -> ScopePermissionMapType:
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
