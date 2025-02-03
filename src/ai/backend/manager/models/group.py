from __future__ import annotations

import asyncio
import enum
import logging
import uuid
from collections.abc import Container
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
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

import aiotools
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
from ai.backend.common.types import ResourceSlot, VFolderID
from ai.backend.logging import BraceStyleAdapter

from ..api.exceptions import VFolderOperationFailed
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
    set_if_set,
    simple_db_mutate,
    simple_db_mutate_returning_item,
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
from .user import ModifyUserInput, UserRole
from .utils import ExtendedAsyncSAEngine, execute_with_retry

if TYPE_CHECKING:
    from .gql import GraphQueryContext
    from .scaling_group import ScalingGroup
    from .storage import StorageSessionManager

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
    sa.Column("total_resource_slots", ResourceSlotColumn(), default="{}"),
    sa.Column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default={},
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
        data = {
            "name": name,
            "type": ProjectType[props.type],
            "description": props.description,
            "is_active": props.is_active,
            "domain_name": props.domain_name,
            "integration_id": props.integration_id,
            "resource_policy": props.resource_policy,
            "container_registry": props.container_registry,
        }
        # set_if_set() applies to optional without defaults
        set_if_set(
            props,
            data,
            "total_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        set_if_set(props, data, "allowed_vfolder_hosts")
        insert_query = sa.insert(groups).values(data)
        return await simple_db_mutate_returning_item(cls, graph_ctx, insert_query, item_cls=Group)


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
        props: ModifyUserInput,
    ) -> ModifyGroup:
        graph_ctx: GraphQueryContext = info.context
        data: Dict[str, Any] = {}
        set_if_set(props, data, "name")
        set_if_set(props, data, "description")
        set_if_set(props, data, "is_active")
        set_if_set(props, data, "domain_name")
        set_if_set(
            props,
            data,
            "total_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        set_if_set(props, data, "allowed_vfolder_hosts")
        set_if_set(props, data, "integration_id")
        set_if_set(props, data, "resource_policy")
        set_if_set(props, data, "container_registry")

        if props.user_update_mode not in (None, Undefined, "add", "remove"):
            raise ValueError("invalid user_update_mode")
        if not props.user_uuids:
            props.user_update_mode = None
        if not data and props.user_update_mode is None:
            return cls(ok=False, msg="nothing to update", group=None)

        async def _do_mutate() -> ModifyGroup:
            async with graph_ctx.db.begin() as conn:
                # TODO: refactor user addition/removal in groups as separate mutations
                #       (to apply since 21.09)
                if props.user_update_mode == "add":
                    values = [{"user_id": uuid, "group_id": gid} for uuid in props.user_uuids]
                    await conn.execute(
                        sa.insert(association_groups_users).values(values),
                    )
                elif props.user_update_mode == "remove":
                    await conn.execute(
                        sa.delete(association_groups_users).where(
                            (association_groups_users.c.user_id.in_(props.user_uuids))
                            & (association_groups_users.c.group_id == gid),
                        ),
                    )
                if data:
                    result = await conn.execute(
                        sa.update(groups).values(data).where(groups.c.id == gid).returning(groups),
                    )
                    if result.rowcount > 0:
                        o = Group.from_row(graph_ctx, result.first())
                        return cls(ok=True, msg="success", group=o)
                    return cls(ok=False, msg="no such group", group=None)
                else:  # updated association_groups_users table
                    return cls(ok=True, msg="success", group=None)

        try:
            return await execute_with_retry(_do_mutate)
        except sa.exc.IntegrityError as e:
            return cls(ok=False, msg=f"integrity error: {e}", group=None)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception as e:
            return cls(ok=False, msg=f"unexpected error: {e}", group=None)


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
        update_query = (
            sa.update(groups)
            .values(
                is_active=False,
                integration_id=None,
            )
            .where(groups.c.id == gid)
        )
        return await simple_db_mutate(cls, ctx, update_query)


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

        async def _pre_func(conn: SAConnection) -> None:
            if await cls.group_vfolder_mounted_to_active_kernels(conn, gid):
                raise RuntimeError(
                    "Some of virtual folders that belong to this group "
                    "are currently mounted to active sessions. "
                    "Terminate them first to proceed removal.",
                )
            if await cls.group_has_active_kernels(conn, gid):
                raise RuntimeError(
                    "Group has some active session. Terminate them first to proceed removal.",
                )
            await cls.delete_vfolders(graph_ctx.db, gid, graph_ctx.storage_manager)
            await cls.delete_kernels(conn, gid)
            await cls.delete_sessions(conn, gid)

        delete_query = sa.delete(groups).where(groups.c.id == gid)
        return await simple_db_mutate(cls, graph_ctx, delete_query, pre_func=_pre_func)

    @classmethod
    async def delete_vfolders(
        cls,
        engine: ExtendedAsyncSAEngine,
        group_id: uuid.UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """
        Delete group's all virtual folders as well as their physical data.

        :param conn: DB connection
        :param group_id: group's UUID to delete virtual folders

        :return: number of deleted rows
        """
        from . import (
            VFolderDeletionInfo,
            VFolderRow,
            VFolderStatusSet,
            initiate_vfolder_deletion,
            vfolder_status_map,
        )

        target_vfs: list[VFolderDeletionInfo] = []
        async with engine.begin_session() as db_session:
            query = sa.select(VFolderRow).where(
                sa.and_(
                    VFolderRow.group == group_id,
                    VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.DELETABLE]),
                )
            )
            result = await db_session.scalars(query)
            rows = cast(list[VFolderRow], result.fetchall())
            for vf in rows:
                target_vfs.append(VFolderDeletionInfo(VFolderID.from_row(vf), vf.host))

        storage_ptask_group = aiotools.PersistentTaskGroup()
        try:
            await initiate_vfolder_deletion(
                engine,
                target_vfs,
                storage_manager,
                storage_ptask_group,
            )
        except VFolderOperationFailed as e:
            log.error("error on deleting vfolder filesystem directory: {0}", e.extra_msg)
            raise
        deleted_count = len(target_vfs)
        if deleted_count > 0:
            log.info("deleted {0} group's virtual folders ({1})", deleted_count, group_id)
        return deleted_count

    @classmethod
    async def delete_kernels(
        cls,
        db_conn: SAConnection,
        group_id: uuid.UUID,
    ) -> int:
        """
        Delete all kernels run from the target groups.

        :param conn: DB connection
        :param group_id: group's UUID to delete kernels

        :return: number of deleted rows
        """
        from . import kernels

        query = sa.delete(kernels).where(kernels.c.group_id == group_id)
        result = await db_conn.execute(query)
        if result.rowcount > 0:
            log.info("deleted {0} group's kernels ({1})", result.rowcount, group_id)
        return result.rowcount

    @classmethod
    async def delete_sessions(
        cls,
        db_conn: SAConnection,
        group_id: uuid.UUID,
    ) -> None:
        """
        Delete all sessions run from the target groups.
        """
        from .session import SessionRow

        stmt = sa.delete(SessionRow).where(SessionRow.group_id == group_id)
        await db_conn.execute(stmt)

    @classmethod
    async def group_vfolder_mounted_to_active_kernels(
        cls,
        db_conn: SAConnection,
        group_id: uuid.UUID,
    ) -> bool:
        """
        Check if no active kernel is using the group's virtual folders.

        :param conn: DB connection
        :param group_id: group's ID

        :return: True if a virtual folder is mounted to active kernels.
        """
        from . import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels, vfolders

        query = sa.select([vfolders.c.id]).select_from(vfolders).where(vfolders.c.group == group_id)
        result = await db_conn.execute(query)
        rows = result.fetchall()
        group_vfolder_ids = [row["id"] for row in rows]
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            )
        )
        async for row in await db_conn.stream(query):
            for _mount in row["mounts"]:
                try:
                    vfolder_id = uuid.UUID(_mount[2])
                    if vfolder_id in group_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    @classmethod
    async def group_has_active_kernels(
        cls,
        db_conn: SAConnection,
        group_id: uuid.UUID,
    ) -> bool:
        """
        Check if the group does not have active kernels.

        :param conn: DB connection
        :param group_id: group's UUID

        :return: True if the group has some active kernels.
        """
        from . import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels

        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            )
        )
        active_kernel_count = await db_conn.scalar(query)
        return True if active_kernel_count > 0 else False


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
    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

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
