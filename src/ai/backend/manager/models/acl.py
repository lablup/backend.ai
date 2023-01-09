from __future__ import annotations

import functools
from enum import Enum
from typing import TYPE_CHECKING, FrozenSet, List, Mapping, Sequence, Type
from uuid import UUID

import graphene
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

from ai.backend.common.types import (
    AbstractPermission,
    DomainPermission,
    ProjectPermission,
    UserPermission,
    VFolderHostPermission,
)

from ..api.context import RootContext
from .base import GUID, Base, EnumValueString, IDColumn, PermissionTypeColumn

if TYPE_CHECKING:
    from .gql import GraphQueryContext


__all__: Sequence[str] = (
    "PredefinedAtomicPermission",
    "get_all_permissions",
    "get_permission_values",
    "AccessibleItem",
    "AccessControlLists",
)


def get_permission_values(permissions: Type[AbstractPermission]) -> List[str]:
    return [perm.value for perm in permissions]


def get_all_permissions() -> Mapping[str, List[str]]:
    return {
        "vfolder_host_permission_list": get_permission_values(VFolderHostPermission),
        "project_permission_list": get_permission_values(ProjectPermission),
        "domain_permission_list": get_permission_values(DomainPermission),
        "user_permission_list": get_permission_values(UserPermission),
    }


class AccessibleItem(str, Enum):
    ANY = "any"

    USER = "user"
    DOMAIN = "domain"
    PROJECT = "project"
    KEYPAIR = "keypair"

    VFOLDER = "vfolder"
    IMAGE = "image"
    SESSION = "session"
    SESSION_TEMPLATE = "session_template"
    RESOURCE_POLICY = "resource_policy"


class AccessControlLists(Base):
    __tablename__ = "access_control_lists"
    id = IDColumn("id")
    subject_type = sa.Column("subject_type", EnumValueString(AccessibleItem), nullable=False)
    subject_id = sa.Column(
        "subject_id", GUID, nullable=False, index=True
    )  # no explicit foreign key yet
    target_type = sa.Column("target_type", EnumValueString(AccessibleItem), nullable=False)
    target_id = sa.Column(
        "target_id", GUID, nullable=False, index=True
    )  # no explicit foreign key yet

    # Do we need any other permission except `BasePermission` ?
    # allowed_actions = sa.Column("allowed_actions", PermissionListColumn(BasePermission), nullable=True)
    # blocked_actions = sa.Column("blocked_actions", PermissionListColumn(BasePermission), nullable=True)
    permission_type = sa.Column("permission_type", PermissionTypeColumn(), nullable=False)
    allowed_actions = sa.Column("allowed_actions", psql.ARRAY(sa.String), nullable=True)
    blocked_actions = sa.Column("blocked_actions", psql.ARRAY(sa.String), nullable=True)

    @property
    def allowed_action_set(self) -> FrozenSet[AbstractPermission]:
        if self.allowed_actions is None:
            return frozenset()
        return frozenset([self.permission_type(action) for action in self.allowed_actions])

    @property
    def blocked_action_set(self) -> FrozenSet[AbstractPermission]:
        if self.blocked_actions is None:
            return frozenset()
        return frozenset([self.permission_type(action) for action in self.blocked_actions])

    @classmethod
    async def check_acl(
        cls,
        root_ctx: RootContext,
        subject_type: AccessibleItem,
        subject_id: UUID,
        target_type: AccessibleItem,
        target_id: UUID,
        action: AbstractPermission,
    ) -> bool:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            cond = (AccessControlLists.subject_id == subject_id) & (
                AccessControlLists.target_id == target_id
            )
            if subject_type != AccessibleItem.ANY:
                cond = cond & (AccessControlLists.subject_type == subject_type)
            if target_type != AccessibleItem.ANY:
                cond = cond & (AccessControlLists.target_type == target_type)
            result = await db_sess.execute(sa.select(AccessControlLists).where(cond))
            acl: AccessControlLists = result.scalars().first()
        return action in (acl.allowed_action_set - acl.blocked_action_set)

    @classmethod
    async def check_merged_acl(
        cls,
        root_ctx: RootContext,
        subjects: Sequence[tuple[AccessibleItem, UUID]],
        target_type: AccessibleItem,
        target_id: UUID,
        action: AbstractPermission,
    ) -> bool:
        if not subjects:
            return False
        async with root_ctx.db.begin_readonly_session() as db_sess:
            cond = AccessControlLists.target_id == target_id
            if target_type != AccessibleItem.ANY:
                cond = cond & (AccessControlLists.target_type == target_type)

            sub_cond = AccessControlLists.subject_id == subjects[0][1]
            if subjects[0][0] != AccessibleItem.ANY:
                sub_cond = sub_cond & (AccessControlLists.subject_type == subjects[0][0])
            for sub_type, sub_id in subjects:
                add_cond = AccessControlLists.subject_id == sub_id
                if sub_type != AccessibleItem.ANY:
                    add_cond = add_cond & (AccessControlLists.subject_type == sub_type)
                sub_cond = sub_cond | add_cond
            cond = cond & sub_cond
            query = sa.select(AccessControlLists).where(cond)
            result = await db_sess.stream_scalars(query)
            acls: list[AccessControlLists] = await result.all()
            merged_allowed_actions: FrozenSet[AbstractPermission] = functools.reduce(
                lambda x, y: x | y, [acl.allowed_action_set for acl in acls]
            )
            merged_blocked_actions: FrozenSet[AbstractPermission] = functools.reduce(
                lambda x, y: x | y, [acl.blocked_action_set for acl in acls]
            )
        return action in (merged_allowed_actions - merged_blocked_actions)

    @classmethod
    async def get_available_actions(
        cls, root_ctx: RootContext, target_type: AccessibleItem
    ) -> list[AbstractPermission]:
        pass

    @classmethod
    async def get_multi_trg_actions(
        cls,
        root_ctx: RootContext,
        subject_type: AccessibleItem,
        subject_id: UUID,
        targets: Sequence[tuple[AccessibleItem, UUID]],
    ) -> Mapping[UUID, FrozenSet[AbstractPermission]]:
        if not targets:
            return {}
        async with root_ctx.db.begin_readonly_session() as db_sess:
            cond = AccessControlLists.subject_id == subject_id
            if subject_type != AccessibleItem.ANY:
                cond = cond & (AccessControlLists.subject_type == subject_type)

            trg_cond = AccessControlLists.target_id == targets[0][1]
            if targets[0][0] != AccessibleItem.ANY:
                trg_cond = trg_cond & (AccessControlLists.subject_type == targets[0][0])
            for trg_type, trg_id in targets:
                add_cond = AccessControlLists.target_id == trg_id
                if trg_type != AccessibleItem.ANY:
                    add_cond = add_cond & (AccessControlLists.target_type == trg_type)
                trg_cond = trg_cond | add_cond
            cond = cond & trg_cond
            query = sa.select(AccessControlLists).where(cond)
            result = await db_sess.stream_scalars(query)
            acls: list[AccessControlLists] = await result.all()

            trg_perm_map = {
                acl.target_id: frozenset(acl.allowed_action_set - acl.blocked_action_set)
                for acl in acls
            }
        return trg_perm_map


class PredefinedAtomicPermission(graphene.ObjectType):
    vfolder_host_permission_list = graphene.List(lambda: graphene.String)

    async def resolve_vfolder_host_permission_list(self, info: graphene.ResolveInfo) -> List[str]:
        return get_permission_values(VFolderHostPermission)

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
    ) -> PredefinedAtomicPermission:
        return cls(**get_all_permissions())
