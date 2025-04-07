from __future__ import annotations

import enum
import logging
import uuid
from collections.abc import Container
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Iterable,
    Optional,
    Self,
    Sequence,
    TypeAlias,
    TypedDict,
    Union,
    cast,
    overload,
    override,
)

import graphene
import sqlalchemy as sa
import trafaret as t
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common import msgpack
from ai.backend.common.types import ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.utils import define_state
from ai.backend.manager.types import OptionalState

from ..defs import RESERVED_DOTFILES
from .base import (
    GUID,
    Base,
    EnumValueType,
    IDColumn,
    ResourceSlotColumn,
    SlugType,
    StructuredJSONColumn,
    VFolderHostPermissionColumn,
    batch_multiresult,
    batch_result,
    mapper_registry,
    privileged_mutation,
)
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    RBACModel,
    ScopeType,
    UserScope,
    get_predefined_roles_in_scope,
    required_permission,
)
from .rbac.context import ClientContext
from .rbac.permission_defs import ProjectPermission
from .user import UserRole

if TYPE_CHECKING:
    from ai.backend.manager.services.groups.actions.create_group import (
        CreateGroupAction,
        CreateGroupActionResult,
    )
    from ai.backend.manager.services.groups.actions.delete_group import (
        DeleteGroupAction,
        DeleteGroupActionResult,
    )
    from ai.backend.manager.services.groups.actions.modify_group import (
        ModifyGroupAction,
        ModifyGroupActionResult,
    )
    from ai.backend.manager.services.groups.actions.purge_group import (
        PurgeGroupAction,
        PurgeGroupActionResult,
    )
    from ai.backend.manager.services.groups.types import GroupData

    from .gql import GraphQueryContext
    from .rbac import ContainerRegistryScope
    from .scaling_group import ScalingGroup

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "groups",
    "GroupRow",
    "association_groups_users",
    "AssocGroupUserRow",
    "resolve_group_name_or_id",
    "Group",
    "GroupInput",
    "ModifyGroupInput",
    "CreateGroup",
    "ModifyGroup",
    "DeleteGroup",
    "GroupDotfile",
    "ProjectType",
    "MAXIMUM_DOTFILE_SIZE",
    "query_group_dotfiles",
    "query_group_domain",
    "verify_dotfile_name",
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB


association_groups_users = sa.Table(
    "association_groups_users",
    mapper_registry.metadata,
    IDColumn(),
    sa.Column(
        "user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "group_id",
        GUID,
        sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.UniqueConstraint("user_id", "group_id", name="uq_association_user_id_group_id"),
)

container_registry_iv = t.Dict({}) | t.Dict({
    t.Key("registry"): t.String(),
    t.Key("project"): t.String(),
})


class AssocGroupUserRow(Base):
    __table__ = association_groups_users
    user = relationship("UserRow", back_populates="groups")
    group = relationship("GroupRow", back_populates="users")


class ProjectType(enum.StrEnum):
    GENERAL = "general"
    MODEL_STORE = "model-store"


groups = sa.Table(
    "groups",
    mapper_registry.metadata,
    IDColumn("id"),
    sa.Column("name", SlugType(length=64, allow_unicode=True, allow_dot=True), nullable=False),
    sa.Column("description", sa.String(length=512)),
    sa.Column("is_active", sa.Boolean, default=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    ),
    #: Field for synchronization with external services.
    sa.Column("integration_id", sa.String(length=512)),
    sa.Column(
        "domain_name",
        sa.String(length=64),
        sa.ForeignKey("domains.name", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    # TODO: separate resource-related fields with new domain resource policy table when needed.
    sa.Column("total_resource_slots", ResourceSlotColumn(), default=dict),
    sa.Column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default=dict,
    ),
    # dotfiles column, \x90 means empty list in msgpack
    sa.Column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    ),
    sa.Column(
        "resource_policy",
        sa.String(length=256),
        sa.ForeignKey("project_resource_policies.name"),
        nullable=False,
    ),
    sa.Column(
        "type",
        EnumValueType(ProjectType),
        nullable=False,
        default=ProjectType.GENERAL,
    ),
    sa.Column(
        "container_registry",
        StructuredJSONColumn(container_registry_iv),
        nullable=True,
        default=None,
    ),
    sa.UniqueConstraint("name", "domain_name", name="uq_groups_name_domain_name"),
)


class GroupRow(Base):
    __table__ = groups
    sessions = relationship("SessionRow", back_populates="group")
    domain = relationship("DomainRow", back_populates="groups")
    sgroup_for_groups_rows = relationship("ScalingGroupForProjectRow", back_populates="project_row")
    users = relationship("AssocGroupUserRow", back_populates="group")
    resource_policy_row = relationship("ProjectResourcePolicyRow", back_populates="projects")
    kernels = relationship("KernelRow", back_populates="group_row")
    networks = relationship(
        "NetworkRow",
        back_populates="project_row",
        primaryjoin="GroupRow.id==foreign(NetworkRow.project)",
    )
    vfolder_rows = relationship(
        "VFolderRow",
        back_populates="group_row",
        primaryjoin="GroupRow.id == foreign(VFolderRow.group)",
    )
    association_container_registries_groups_rows = relationship(
        "AssociationContainerRegistriesGroupsRow",
        back_populates="group_row",
        primaryjoin="GroupRow.id == foreign(AssociationContainerRegistriesGroupsRow.group_id)",
    )

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        project_id: uuid.UUID,
        load_resource_policy=False,
    ) -> "GroupRow":
        query = sa.select(GroupRow).filter(GroupRow.id == project_id)
        if load_resource_policy:
            query = query.options(selectinload(GroupRow.resource_policy_row))
        row = await session.scalar(query)
        if not row:
            raise NoResultFound

        return row


@dataclass
class ProjectModel(RBACModel[ProjectPermission]):
    id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    modified_at: datetime
    domain_name: str
    type: str

    _integration_id: str
    _total_resource_slots: dict
    _allowed_vfolder_hosts: dict
    _dotfiles: str
    _resource_policy: str
    _container_registry: dict

    _permissions: frozenset[ProjectPermission] = field(default_factory=frozenset)

    @property
    def permissions(self) -> Container[ProjectPermission]:
        return self._permissions

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def integration_id(self) -> str:
        return self._integration_id

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def total_resource_slots(self) -> dict:
        return self._total_resource_slots

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def allowed_vfolder_hosts(self) -> dict:
        return self._allowed_vfolder_hosts

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def dotfiles(self) -> str:
        return self._dotfiles

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def resource_policy(self) -> str:
        return self._resource_policy

    @property
    @required_permission(ProjectPermission.READ_SENSITIVE_ATTRIBUTE)
    def container_registry(self) -> dict:
        return self._container_registry

    @classmethod
    def from_row(cls, row: GroupRow, permissions: Iterable[ProjectPermission]) -> Self:
        return cls(
            id=row.id,
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            modified_at=row.modified_at,
            domain_name=row.domain_name,
            type=row.type,
            _integration_id=row.integration_id,
            _total_resource_slots=row.total_resource_slots,
            _allowed_vfolder_hosts=row.allowed_vfolder_hosts,
            _dotfiles=row.dotfiles,
            _resource_policy=row.resource_policy,
            _container_registry=row.container_registry,
            _permissions=frozenset(permissions),
        )


def _build_group_query(cond: sa.sql.BinaryExpression, domain_name: str) -> sa.sql.Select:
    query = (
        sa.select([groups.c.id])
        .select_from(groups)
        .where(
            cond & (groups.c.domain_name == domain_name),
        )
    )
    return query


async def resolve_group_name_or_id(
    db_conn: SAConnection,
    domain_name: str,
    value: Union[str, uuid.UUID],
) -> Optional[uuid.UUID]:
    match value:
        case uuid.UUID():
            cond = groups.c.id == value
        case str():
            cond = groups.c.name == value
        case _:
            raise TypeError("unexpected type for group_name_or_id")
    query = _build_group_query(cond, domain_name)
    return await db_conn.scalar(query)


@overload
async def resolve_groups(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[uuid.UUID],
) -> Iterable[uuid.UUID]: ...


@overload
async def resolve_groups(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[str],
) -> Iterable[uuid.UUID]: ...


async def resolve_groups(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[uuid.UUID] | Iterable[str],
) -> Iterable[uuid.UUID]:
    listed_val = [*values]
    match listed_val:
        case [uuid.UUID(), *_]:
            query = _build_group_query((groups.c.id.in_(listed_val)), domain_name)
        case [str(), *_]:
            query = _build_group_query((groups.c.name.in_(listed_val)), domain_name)
        case []:
            return []
        case _:
            raise TypeError("unexpected type for group_name_or_id")

    rows = (await db_conn.execute(query)).fetchall()
    return_val = [row["id"] for row in rows]

    return return_val


class Group(graphene.ObjectType):
    id = graphene.UUID()
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    domain_name = graphene.String()
    total_resource_slots = graphene.JSONString()
    allowed_vfolder_hosts = graphene.JSONString()
    integration_id = graphene.String()
    resource_policy = graphene.String()
    type = graphene.String(description="Added in 24.03.0.")
    container_registry = graphene.JSONString(description="Added in 24.03.0.")

    scaling_groups = graphene.List(lambda: graphene.String)

    @classmethod
    def from_row(cls, graph_ctx: GraphQueryContext, row: Row) -> Optional[Group]:
        if row is None:
            return None
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            domain_name=row["domain_name"],
            total_resource_slots=(
                row["total_resource_slots"].to_json()
                if row["total_resource_slots"] is not None
                else {}
            ),
            allowed_vfolder_hosts=row["allowed_vfolder_hosts"].to_json(),
            integration_id=row["integration_id"],
            resource_policy=row["resource_policy"],
            type=row["type"].name,
            container_registry=row["container_registry"],
        )

    @classmethod
    def from_dto(cls, dto: Optional[GroupData]) -> Optional[Self]:
        if dto is None:
            return None
        return cls(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            is_active=dto.is_active,
            created_at=dto.created_at,
            modified_at=dto.modified_at,
            domain_name=dto.domain_name,
            total_resource_slots=dto.total_resource_slots.to_json()
            if dto.total_resource_slots
            else {},
            allowed_vfolder_hosts=dto.allowed_vfolder_hosts.to_json(),
            integration_id=dto.integration_id,
            resource_policy=dto.resource_policy,
            type=dto.type.name,
            container_registry=dto.container_registry,
        )

    async def resolve_scaling_groups(self, info: graphene.ResolveInfo) -> Sequence[ScalingGroup]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "ScalingGroup.by_group",
        )
        sgroups = await loader.load(self.id)
        return [sg.name for sg in sgroups]

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        type: list[ProjectType] = [ProjectType.GENERAL],
    ) -> Sequence[Group]:
        query = sa.select([groups]).select_from(groups).where(groups.c.type.in_(type))
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if is_active is not None:
            query = query.where(groups.c.is_active == is_active)
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_id(
        cls,
        graph_ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
        *,
        domain_name: Optional[str] = None,
    ) -> Sequence[Group | None]:
        query = sa.select([groups]).select_from(groups).where(groups.c.id.in_(group_ids))
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_result(
                graph_ctx,
                conn,
                query,
                cls,
                group_ids,
                lambda row: row["id"],
            )

    @classmethod
    async def batch_load_by_name(
        cls,
        graph_ctx: GraphQueryContext,
        group_names: Sequence[str],
        *,
        domain_name: Optional[str] = None,
    ) -> Sequence[Sequence[Group | None]]:
        query = sa.select([groups]).select_from(groups).where(groups.c.name.in_(group_names))
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx,
                conn,
                query,
                cls,
                group_names,
                lambda row: row["name"],
            )

    @classmethod
    async def batch_load_by_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_ids: Sequence[uuid.UUID],
        *,
        type: list[ProjectType] | None = None,
    ) -> Sequence[Sequence[Group | None]]:
        if type is None:
            _type = [ProjectType.GENERAL]
        else:
            _type = type
        j = sa.join(
            groups,
            association_groups_users,
            groups.c.id == association_groups_users.c.group_id,
        )
        query = (
            sa.select([groups, association_groups_users.c.user_id])
            .select_from(j)
            .where(association_groups_users.c.user_id.in_(user_ids) & (groups.c.type.in_(_type)))
        )
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx,
                conn,
                query,
                cls,
                user_ids,
                lambda row: row["user_id"],
            )

    @classmethod
    async def get_groups_for_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_id: uuid.UUID,
    ) -> Sequence[Group]:
        j = sa.join(
            groups,
            association_groups_users,
            groups.c.id == association_groups_users.c.group_id,
        )
        query = (
            sa.select([groups]).select_from(j).where(association_groups_users.c.user_id == user_id)
        )
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]


class GroupInput(graphene.InputObjectType):
    type = graphene.String(
        required=False,
        default_value="GENERAL",
        description=(
            f"Added in 24.03.0. Available values: {', '.join([p.name for p in ProjectType])}"
        ),
    )
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    domain_name = graphene.String(required=True)
    total_resource_slots = graphene.JSONString(required=False, default_value={})
    allowed_vfolder_hosts = graphene.JSONString(required=False, default_value={})
    integration_id = graphene.String(required=False, default_value="")
    resource_policy = graphene.String(required=False, default_value="default")
    container_registry = graphene.JSONString(
        required=False, default_value={}, description="Added in 24.03.0"
    )

    def to_action(self, name: str) -> CreateGroupAction:
        def value_or_none(value):
            return value if value is not Undefined else None

        type_val = None if self.type is Undefined else ProjectType[self.type]
        description_val = value_or_none(self.description)
        is_active_val = value_or_none(self.is_active)
        total_resource_slots_val = (
            None
            if self.total_resource_slots is Undefined
            else ResourceSlot.from_user_input(self.total_resource_slots, None)
        )
        allowed_vfolder_hosts_val = value_or_none(self.allowed_vfolder_hosts)
        integration_id_val = value_or_none(self.integration_id)
        resource_policy_val = value_or_none(self.resource_policy)
        container_registry_val = value_or_none(self.container_registry)

        return CreateGroupAction(
            name=name,
            domain_name=self.domain_name,
            type=type_val,
            description=description_val,
            is_active=is_active_val,
            total_resource_slots=total_resource_slots_val,
            allowed_vfolder_hosts=allowed_vfolder_hosts_val,
            integration_id=integration_id_val,
            resource_policy=resource_policy_val,
            container_registry=container_registry_val,
        )


class ModifyGroupInput(graphene.InputObjectType):
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    domain_name = graphene.String(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    user_update_mode = graphene.String(required=False)
    user_uuids = graphene.List(lambda: graphene.String, required=False)
    allowed_vfolder_hosts = graphene.JSONString(required=False)
    integration_id = graphene.String(required=False)
    resource_policy = graphene.String(required=False)
    container_registry = graphene.JSONString(
        required=False, default_value={}, description="Added in 24.03.0"
    )

    def to_action(self, group_id: uuid.UUID) -> ModifyGroupAction:
        def value_or_none(value):
            return value if value is not Undefined else None

        return ModifyGroupAction(
            group_id=group_id,
            name=OptionalState(
                "name",
                define_state(self.name),
                value_or_none(self.name),
            ),
            domain_name=OptionalState(
                "domain_name",
                define_state(self.domain_name),
                value_or_none(self.domain_name),
            ),
            description=OptionalState(
                "description",
                define_state(self.description),
                value_or_none(self.description),
            ),
            is_active=OptionalState(
                "is_active",
                define_state(self.is_active),
                value_or_none(self.is_active),
            ),
            total_resource_slots=OptionalState(
                "total_resource_slots",
                define_state(self.total_resource_slots),
                None
                if self.total_resource_slots is Undefined
                else ResourceSlot.from_user_input(self.total_resource_slots, None),
            ),
            user_update_mode=OptionalState(
                "user_update_mode",
                define_state(self.user_update_mode),
                value_or_none(self.user_update_mode),
            ),
            user_uuids=OptionalState(
                "user_uuids",
                define_state(self.user_uuids),
                value_or_none(self.user_uuids),
            ),
            allowed_vfolder_hosts=OptionalState(
                "allowed_vfolder_hosts",
                define_state(self.allowed_vfolder_hosts),
                value_or_none(self.allowed_vfolder_hosts),
            ),
            integration_id=OptionalState(
                "integration_id",
                define_state(self.integration_id),
                value_or_none(self.integration_id),
            ),
            resource_policy=OptionalState(
                "resource_policy",
                define_state(self.resource_policy),
                value_or_none(self.resource_policy),
            ),
            container_registry=OptionalState(
                "container_registry",
                define_state(self.container_registry),
                value_or_none(self.container_registry),
            ),
        )


class CreateGroup(graphene.Mutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        name = graphene.String(required=True)
        props = GroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    group = graphene.Field(lambda: Group, required=False)

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda name, props, **kwargs: (props.domain_name, None),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: GroupInput,
    ) -> CreateGroup:
        graph_ctx: GraphQueryContext = info.context

        action = props.to_action(name)
        res: CreateGroupActionResult = (
            await graph_ctx.processors.group.create_group.wait_for_complete(action)
        )

        return cls(
            ok=res.success,
            msg="success" if res.success else "failed",
            group=Group.from_dto(res.data) if res.success else None,
        )


class ModifyGroup(graphene.Mutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)
        props = ModifyGroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    group = graphene.Field(lambda: Group, required=False)

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        gid: uuid.UUID,
        props: ModifyGroupInput,
    ) -> ModifyGroup:
        graph_ctx: GraphQueryContext = info.context

        action = props.to_action(gid)
        res: ModifyGroupActionResult = (
            await graph_ctx.processors.group.modify_group.wait_for_complete(action)
        )

        return cls(
            ok=res.success,
            msg="success" if res.success else "failed",
            group=Group.from_dto(res.data) if res.success else None,
        )


class DeleteGroup(graphene.Mutation):
    """
    Instead of deleting the group, just mark it as inactive.
    """

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(cls, root, info: graphene.ResolveInfo, gid: uuid.UUID) -> DeleteGroup:
        ctx: GraphQueryContext = info.context
        res: DeleteGroupActionResult = await ctx.processors.group.delete_group.wait_for_complete(
            DeleteGroupAction(gid)
        )

        return cls(ok=res.success, msg="success" if res.success else "failed")


class PurgeGroup(graphene.Mutation):
    """
    Completely deletes a group from DB.

    Group's vfolders and their data will also be lost
    as well as the kernels run from the group.
    There is no migration of the ownership for group folders.
    """

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(cls, root, info: graphene.ResolveInfo, gid: uuid.UUID) -> PurgeGroup:
        graph_ctx: GraphQueryContext = info.context

        res: PurgeGroupActionResult = (
            await graph_ctx.processors.group.purge_group.wait_for_complete(PurgeGroupAction(gid))
        )

        return cls(
            ok=res.success,
            msg="success" if res.success else "failed",
        )


class GroupDotfile(TypedDict):
    data: str
    path: str
    perm: str


async def query_group_dotfiles(
    db_conn: SAConnection,
    group_id: Union[GUID, uuid.UUID],
) -> tuple[list[GroupDotfile], int]:
    query = sa.select([groups.c.dotfiles]).select_from(groups).where(groups.c.id == group_id)
    packed_dotfile = await db_conn.scalar(query)
    if packed_dotfile is None:
        return [], MAXIMUM_DOTFILE_SIZE
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


async def query_group_domain(
    db_conn: SAConnection,
    group_id: Union[GUID, uuid.UUID],
) -> str:
    query = sa.select([groups.c.domain_name]).select_from(groups).where(groups.c.id == group_id)
    domain = await db_conn.scalar(query)
    return domain


def verify_dotfile_name(dotfile: str) -> bool:
    if dotfile in RESERVED_DOTFILES:
        return False
    return True


ALL_PROJECT_PERMISSIONS = frozenset([perm for perm in ProjectPermission])
OWNER_PERMISSIONS: frozenset[ProjectPermission] = ALL_PROJECT_PERMISSIONS
ADMIN_PERMISSIONS: frozenset[ProjectPermission] = ALL_PROJECT_PERMISSIONS
MONITOR_PERMISSIONS: frozenset[ProjectPermission] = frozenset([
    ProjectPermission.READ_ATTRIBUTE,
    ProjectPermission.READ_SENSITIVE_ATTRIBUTE,
    ProjectPermission.UPDATE_ATTRIBUTE,
])
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[ProjectPermission] = frozenset([
    ProjectPermission.READ_ATTRIBUTE
])
MEMBER_PERMISSIONS: frozenset[ProjectPermission] = frozenset([ProjectPermission.READ_ATTRIBUTE])

WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)


@dataclass
class ProjectPermissionContext(AbstractPermissionContext[ProjectPermission, GroupRow, uuid.UUID]):
    registry_id_to_additional_permission_map: dict[uuid.UUID, frozenset[ProjectPermission]] = field(
        default_factory=dict
    )

    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.registry_id_to_additional_permission_map:
            registry_id = list(self.registry_id_to_additional_permission_map)[0]

            cond = _OR_coalesce(
                cond,
                GroupRow.association_container_registries_groups_rows.any(
                    AssociationContainerRegistriesGroupsRow.registry_id == registry_id
                ),
            )
        if self.domain_name_to_permission_map:
            cond = _OR_coalesce(
                cond, GroupRow.domain_name.in_(self.domain_name_to_permission_map.keys())
            )
        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, GroupRow.id.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, GroupRow.id.in_(self.object_id_to_overriding_permission_map.keys())
            )
        return cond

    async def build_query(self) -> sa.sql.Select | None:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(GroupRow).where(cond)

    async def calculate_final_permission(self, rbac_obj: GroupRow) -> frozenset[ProjectPermission]:
        project_row = rbac_obj
        project_id = cast(uuid.UUID, project_row.id)
        permissions: frozenset[ProjectPermission] = frozenset()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(project_id)
        ) is not None:
            permissions = overriding_perm
        else:
            permissions |= self.object_id_to_additional_permission_map.get(project_id, set())
            permissions |= self.domain_name_to_permission_map.get(project_row.domain_name, set())
        return permissions


class ProjectPermissionContextBuilder(
    AbstractPermissionContextBuilder[ProjectPermission, ProjectPermissionContext]
):
    db_session: AsyncSession

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[ProjectPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        permissions = await self._calculate_permission_by_predefined_roles(roles)
        return permissions

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> ProjectPermissionContext:
        from .domain import DomainRow

        perm_ctx = ProjectPermissionContext()
        _domain_query_stmt = sa.select(DomainRow).options(load_only(DomainRow.name))
        for row in await self.db_session.scalars(_domain_query_stmt):
            to_be_merged = await self.build_ctx_in_domain_scope(ctx, DomainScope(row.name))
            perm_ctx.merge(to_be_merged)
        return perm_ctx

    @override
    async def build_ctx_in_domain_scope(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> ProjectPermissionContext:
        permissions = await self.calculate_permission(ctx, scope)
        return ProjectPermissionContext(
            domain_name_to_permission_map={scope.domain_name: permissions}
        )

    @override
    async def build_ctx_in_project_scope(
        self, ctx: ClientContext, scope: ProjectScope
    ) -> ProjectPermissionContext:
        permissions = await self.calculate_permission(ctx, scope)
        return ProjectPermissionContext(
            object_id_to_additional_permission_map={scope.project_id: permissions}
        )

    @override
    async def build_ctx_in_user_scope(
        self, ctx: ClientContext, scope: UserScope
    ) -> ProjectPermissionContext:
        return ProjectPermissionContext()

    async def build_ctx_in_container_registry_scope(
        self, ctx: ClientContext, scope: ContainerRegistryScope
    ) -> ProjectPermissionContext:
        permissions = MEMBER_PERMISSIONS
        return ProjectPermissionContext(
            registry_id_to_additional_permission_map={scope.registry_id: permissions}
        )

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[ProjectPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[ProjectPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[ProjectPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[ProjectPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[ProjectPermission]:
        return MEMBER_PERMISSIONS


async def get_projects(
    target_scope: ScopeType,
    requested_permission: ProjectPermission,
    project_id: Optional[uuid.UUID] = None,
    project_name: Optional[str] = None,
    *,
    ctx: ClientContext,
    db_conn: SAConnection,
) -> list[ProjectModel]:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        builder = ProjectPermissionContextBuilder(db_session)
        permission_ctx = await builder.build(ctx, target_scope, requested_permission)
        query_stmt = await permission_ctx.build_query()
        if query_stmt is None:
            return []
        if project_id is not None:
            query_stmt = query_stmt.where(GroupRow.id == project_id)
        if project_name is not None:
            query_stmt = query_stmt.where(GroupRow.name == project_name)
        result: list[ProjectModel] = []
        async for row in await db_session.stream_scalars(query_stmt):
            permissions = await permission_ctx.calculate_final_permission(row)
            result.append(ProjectModel.from_row(row, permissions))
    return result


async def get_permission_ctx(
    db_conn: SAConnection,
    ctx: ClientContext,
    requested_permission: ProjectPermission,
    target_scope: ScopeType,
    container_registry_scope: Optional[ContainerRegistryScope] = None,
) -> ProjectPermissionContext:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        builder = ProjectPermissionContextBuilder(db_session)

        if container_registry_scope is not None:
            return await builder.build_ctx_in_container_registry_scope(
                ctx, container_registry_scope
            )
        else:
            return await builder.build(ctx, target_scope, requested_permission)
