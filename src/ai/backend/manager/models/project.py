from __future__ import annotations

import asyncio
import enum
import logging
import re
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Optional,
    Sequence,
    TypedDict,
    Union,
    overload,
)

import aiotools
import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.orm import relationship

from ai.backend.common import msgpack
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ResourceSlot, VFolderID

from ..api.exceptions import VFolderOperationFailed
from ..defs import RESERVED_DOTFILES
from .base import (
    GUID,
    Base,
    EnumValueType,
    IDColumn,
    PaginatedConnectionField,
    ResourceSlotColumn,
    VFolderHostPermissionColumn,
    batch_multiresult,
    batch_result,
    generate_sql_info_for_gql_connection,
    mapper_registry,
    privileged_mutation,
    set_if_set,
    simple_db_mutate,
    simple_db_mutate_returning_item,
)
from .gql_relay import (
    AsyncNode,
    Connection,
    ConnectionResolverResult,
)
from .storage import StorageSessionManager
from .user import ModifyUserInput, UserConnection, UserNode, UserRole
from .utils import ExtendedAsyncSAEngine, execute_with_retry

if TYPE_CHECKING:
    from .gql import GraphQueryContext
    from .scaling_group import ScalingGroup

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


__all__: Sequence[str] = (
    "projects",
    "association_projects_users",
    "resolve_project_name_or_id",
    "Project",
    "ProjectRow",
    "ProjectInput",
    "ModifyProjectInput",
    "CreateProject",
    "ModifyProject",
    "DeleteProject",
    "ProjectDotfile",
    "ProjectType",
    "MAXIMUM_DOTFILE_SIZE",
    "query_project_dotfiles",
    "query_project_domain",
    "verify_dotfile_name",
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB
_rx_slug = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$")

association_projects_users = sa.Table(
    "association_projects_users",
    mapper_registry.metadata,
    IDColumn(),
    sa.Column(
        "user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "project_id",
        GUID,
        sa.ForeignKey("projects.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.UniqueConstraint("user_id", "project_id", name="uq_association_user_id_project_id"),
)


class AssocProjectUserRow(Base):
    __table__ = association_projects_users
    user = relationship("UserRow", back_populates="projects")
    project = relationship("ProjectRow", back_populates="users")


class ProjectType(enum.StrEnum):
    GENERAL = "general"
    MODEL_STORE = "model-store"


projects = sa.Table(
    "projects",
    mapper_registry.metadata,
    IDColumn("id"),
    sa.Column("name", sa.String(length=64), nullable=False),
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
    sa.UniqueConstraint("name", "domain_name", name="uq_projects_name_domain_name"),
)


class ProjectRow(Base):
    __table__ = projects
    sessions = relationship("SessionRow", back_populates="project")
    domain = relationship("DomainRow", back_populates="projects")
    scaling_groups = relationship(
        "ScalingGroupRow", secondary="sgroups_for_projects", back_populates="projects"
    )
    users = relationship("AssocProjectUserRow", back_populates="project")
    resource_policy_row = relationship("ProjectResourcePolicyRow", back_populates="projects")


def _build_project_query(cond: sa.sql.BinaryExpression, domain_name: str) -> sa.sql.Select:
    query = (
        sa.select([projects.c.id])
        .select_from(projects)
        .where(
            cond & (projects.c.domain_name == domain_name),
        )
    )
    return query


async def resolve_project_name_or_id(
    db_conn: SAConnection,
    domain_name: str,
    value: Union[str, uuid.UUID],
) -> Optional[uuid.UUID]:
    match value:
        case uuid.UUID():
            cond = projects.c.id == value
        case str():
            cond = projects.c.name == value
        case _:
            raise TypeError("unexpected type for project_name_or_id")
    query = _build_project_query(cond, domain_name)
    return await db_conn.scalar(query)


@overload
async def resolve_projects(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[uuid.UUID],
) -> Iterable[uuid.UUID]: ...


@overload
async def resolve_projects(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[str],
) -> Iterable[uuid.UUID]: ...


async def resolve_projects(
    db_conn: SAConnection,
    domain_name: str,
    values: Iterable[uuid.UUID] | Iterable[str],
) -> Iterable[uuid.UUID]:
    listed_val = [*values]
    match listed_val:
        case [uuid.UUID(), *_]:
            query = _build_project_query((projects.c.id.in_(listed_val)), domain_name)
        case [str(), *_]:
            query = _build_project_query((projects.c.name.in_(listed_val)), domain_name)
        case []:
            return []
        case _:
            raise TypeError("unexpected type for project_name_or_id")

    rows = (await db_conn.execute(query)).fetchall()
    return_val = [row["id"] for row in rows]

    return return_val


class Project(graphene.ObjectType):
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
    type = graphene.String(description="Added since 24.03.0.")

    scaling_groups = graphene.List(lambda: graphene.String)

    @classmethod
    def from_row(cls, graph_ctx: GraphQueryContext, row: Row) -> Optional[Project]:
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
            total_resource_slots=row["total_resource_slots"].to_json(),
            allowed_vfolder_hosts=row["allowed_vfolder_hosts"].to_json(),
            integration_id=row["integration_id"],
            resource_policy=row["resource_policy"],
            type=row["type"].name,
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
        domain_name: str = None,
        is_active: bool = None,
        type: list[ProjectType] = [ProjectType.GENERAL],
    ) -> Sequence[Project]:
        query = sa.select([projects]).select_from(projects).where(projects.c.type.in_(type))
        if domain_name is not None:
            query = query.where(projects.c.domain_name == domain_name)
        if is_active is not None:
            query = query.where(projects.c.is_active == is_active)
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
        project_ids: Sequence[uuid.UUID],
        *,
        domain_name: str = None,
    ) -> Sequence[Project | None]:
        query = sa.select([projects]).select_from(projects).where(projects.c.id.in_(project_ids))
        if domain_name is not None:
            query = query.where(projects.c.domain_name == domain_name)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_result(
                graph_ctx,
                conn,
                query,
                cls,
                project_ids,
                lambda row: row["id"],
            )

    @classmethod
    async def batch_load_by_name(
        cls,
        graph_ctx: GraphQueryContext,
        project_names: Sequence[str],
        *,
        domain_name: str = None,
    ) -> Sequence[Sequence[Project | None]]:
        query = (
            sa.select([projects]).select_from(projects).where(projects.c.name.in_(project_names))
        )
        if domain_name is not None:
            query = query.where(projects.c.domain_name == domain_name)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx,
                conn,
                query,
                cls,
                project_names,
                lambda row: row["name"],
            )

    @classmethod
    async def batch_load_by_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_ids: Sequence[uuid.UUID],
        type: list[ProjectType] = [ProjectType.GENERAL],
    ) -> Sequence[Sequence[Project | None]]:
        j = sa.join(
            projects,
            association_projects_users,
            projects.c.id == association_projects_users.c.project_id,
        )
        query = (
            sa.select([projects, association_projects_users.c.user_id])
            .select_from(j)
            .where(association_projects_users.c.user_id.in_(user_ids) & (projects.c.type.in_(type)))
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
    async def get_projects_for_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_id: uuid.UUID,
    ) -> Sequence[Project]:
        j = sa.join(
            projects,
            association_projects_users,
            projects.c.id == association_projects_users.c.project_id,
        )
        query = (
            sa.select([projects])
            .select_from(j)
            .where(association_projects_users.c.user_id == user_id)
        )
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]


class ProjectInput(graphene.InputObjectType):
    type = graphene.String(
        required=False,
        default_value="GENERAL",
        description=(
            f"Added since 24.03.0. Available values: {', '.join([p.name for p in ProjectType])}"
        ),
    )
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    domain_name = graphene.String(required=True)
    total_resource_slots = graphene.JSONString(required=False, default_value={})
    allowed_vfolder_hosts = graphene.JSONString(required=False, default_value={})
    integration_id = graphene.String(required=False, default_value="")
    resource_policy = graphene.String(required=False, default_value="default")


class ModifyProjectInput(graphene.InputObjectType):
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


class CreateProject(graphene.Mutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        name = graphene.String(required=True)
        props = ProjectInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    project = graphene.Field(lambda: Project, required=False)

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
        props: ProjectInput,
    ) -> CreateProject:
        if _rx_slug.search(name) is None:
            raise ValueError("invalid name format. slug format required.")
        graph_ctx: GraphQueryContext = info.context
        data = {
            "name": name,
            "type": ProjectType[props.type],
            "description": props.description,
            "is_active": props.is_active,
            "domain_name": props.domain_name,
            "integration_id": props.integration_id,
            "resource_policy": props.resource_policy,
        }
        # set_if_set() applies to optional without defaults
        set_if_set(
            props,
            data,
            "total_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        set_if_set(props, data, "allowed_vfolder_hosts")
        insert_query = sa.insert(projects).values(data)
        return await simple_db_mutate_returning_item(cls, graph_ctx, insert_query, item_cls=Project)


class ModifyProject(graphene.Mutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)
        props = ModifyProjectInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    project = graphene.Field(lambda: Project, required=False)

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
    ) -> ModifyProject:
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

        if "name" in data and _rx_slug.search(data["name"]) is None:
            raise ValueError("invalid name format. slug format required.")
        if props.user_update_mode not in (None, Undefined, "add", "remove"):
            raise ValueError("invalid user_update_mode")
        if not props.user_uuids:
            props.user_update_mode = None
        if not data and props.user_update_mode is None:
            return cls(ok=False, msg="nothing to update", project=None)

        async def _do_mutate() -> ModifyProject:
            async with graph_ctx.db.begin() as conn:
                # TODO: refactor user addition/removal in projects as separate mutations
                #       (to apply since 21.09)
                if props.user_update_mode == "add":
                    values = [{"user_id": uuid, "project_id": gid} for uuid in props.user_uuids]
                    await conn.execute(
                        sa.insert(association_projects_users).values(values),
                    )
                elif props.user_update_mode == "remove":
                    await conn.execute(
                        sa.delete(association_projects_users).where(
                            (association_projects_users.c.user_id.in_(props.user_uuids))
                            & (association_projects_users.c.project_id == gid),
                        ),
                    )
                if data:
                    result = await conn.execute(
                        sa.update(projects)
                        .values(data)
                        .where(projects.c.id == gid)
                        .returning(projects),
                    )
                    if result.rowcount > 0:
                        o = Project.from_row(graph_ctx, result.first())
                        return cls(ok=True, msg="success", project=o)
                    return cls(ok=False, msg="no such project", project=None)
                else:  # updated association_projects_users table
                    return cls(ok=True, msg="success", project=None)

        try:
            return await execute_with_retry(_do_mutate)
        except sa.exc.IntegrityError as e:
            return cls(ok=False, msg=f"integrity error: {e}", project=None)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception as e:
            return cls(ok=False, msg=f"unexpected error: {e}", project=None)


class DeleteProject(graphene.Mutation):
    """
    Instead of deleting the project, just mark it as inactive.
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
    async def mutate(cls, root, info: graphene.ResolveInfo, gid: uuid.UUID) -> DeleteProject:
        ctx: GraphQueryContext = info.context
        update_query = (
            sa.update(projects)
            .values(
                is_active=False,
                integration_id=None,
            )
            .where(projects.c.id == gid)
        )
        return await simple_db_mutate(cls, ctx, update_query)


class PurgeProject(graphene.Mutation):
    """
    Completely deletes a project from DB.

    Project's vfolders and their data will also be lost
    as well as the kernels run from the project.
    There is no migration of the ownership for project folders.
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
    async def mutate(cls, root, info: graphene.ResolveInfo, gid: uuid.UUID) -> PurgeProject:
        graph_ctx: GraphQueryContext = info.context

        async def _pre_func(conn: SAConnection) -> None:
            if await cls.project_vfolder_mounted_to_active_kernels(conn, gid):
                raise RuntimeError(
                    "Some of virtual folders that belong to this project "
                    "are currently mounted to active sessions. "
                    "Terminate them first to proceed removal.",
                )
            if await cls.project_has_active_kernels(conn, gid):
                raise RuntimeError(
                    "Project has some active session. Terminate them first to proceed removal.",
                )
            await cls.delete_vfolders(graph_ctx.db, gid, graph_ctx.storage_manager)
            await cls.delete_kernels(conn, gid)

        delete_query = sa.delete(projects).where(projects.c.id == gid)
        return await simple_db_mutate(cls, graph_ctx, delete_query, pre_func=_pre_func)

    @classmethod
    async def delete_vfolders(
        cls,
        engine: ExtendedAsyncSAEngine,
        project_id: uuid.UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """
        Delete project's all virtual folders as well as their physical data.

        :param conn: DB connection
        :param project_id: project's UUID to delete virtual folders

        :return: number of deleted rows
        """
        from . import VFolderDeletionInfo, initiate_vfolder_purge, vfolders

        query = (
            sa.select([vfolders.c.id, vfolders.c.host])
            .select_from(vfolders)
            .where(vfolders.c.group == project_id)
        )
        async with engine.begin_session() as db_conn:
            result = await db_conn.execute(query)
            target_vfs = result.fetchall()
            delete_query = sa.delete(vfolders).where(vfolders.c.project_id == project_id)
            result = await db_conn.execute(delete_query)

        storage_ptask_group = aiotools.PersistentTaskGroup()
        try:
            await initiate_vfolder_purge(
                engine,
                [VFolderDeletionInfo(VFolderID.from_row(vf), vf["host"]) for vf in target_vfs],
                storage_manager,
                storage_ptask_group,
            )
        except VFolderOperationFailed as e:
            log.error("error on deleting vfolder filesystem directory: {0}", e.extra_msg)
            raise
        deleted_count = len(target_vfs)
        if deleted_count > 0:
            log.info("deleted {0} project's virtual folders ({1})", deleted_count, project_id)
        return deleted_count

    @classmethod
    async def delete_kernels(
        cls,
        db_conn: SAConnection,
        project_id: uuid.UUID,
    ) -> int:
        """
        Delete all kernels run from the target projects.

        :param conn: DB connection
        :param project_id: project's UUID to delete kernels

        :return: number of deleted rows
        """
        from . import kernels

        query = sa.delete(kernels).where(kernels.c.project_id == project_id)
        result = await db_conn.execute(query)
        if result.rowcount > 0:
            log.info("deleted {0} project's kernels ({1})", result.rowcount, project_id)
        return result.rowcount

    @classmethod
    async def project_vfolder_mounted_to_active_kernels(
        cls,
        db_conn: SAConnection,
        project_id: uuid.UUID,
    ) -> bool:
        """
        Check if no active kernel is using the project's virtual folders.

        :param conn: DB connection
        :param project_id: project's ID

        :return: True if a virtual folder is mounted to active kernels.
        """
        from . import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels, vfolders

        query = (
            sa.select([vfolders.c.id]).select_from(vfolders).where(vfolders.c.group == project_id)
        )
        result = await db_conn.execute(query)
        rows = result.fetchall()
        project_vfolder_ids = [row["id"] for row in rows]
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(
                (kernels.c.project_id == project_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            )
        )
        async for row in await db_conn.stream(query):
            for _mount in row["mounts"]:
                try:
                    vfolder_id = uuid.UUID(_mount[2])
                    if vfolder_id in project_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    @classmethod
    async def project_has_active_kernels(
        cls,
        db_conn: SAConnection,
        project_id: uuid.UUID,
    ) -> bool:
        """
        Check if the project does not have active kernels.

        :param conn: DB connection
        :param project_id: project's UUID

        :return: True if the project has some active kernels.
        """
        from . import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels

        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.project_id == project_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            )
        )
        active_kernel_count = await db_conn.scalar(query)
        return True if active_kernel_count > 0 else False


class ProjectNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

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
    scaling_groups = graphene.List(
        lambda: graphene.String,
    )

    user_nodes = PaginatedConnectionField(
        UserConnection,
    )

    @classmethod
    def from_row(cls, row: ProjectRow) -> ProjectNode:
        return cls(
            id=row.id,
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            modified_at=row.modified_at,
            domain_name=row.domain_name,
            total_resource_slots=row.total_resource_slots or {},
            allowed_vfolder_hosts=row.allowed_vfolder_hosts or {},
            integration_id=row.integration_id,
            resource_policy=row.resource_policy,
        )

    async def resolve_scaling_groups(self, info: graphene.ResolveInfo) -> Sequence[ScalingGroup]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx,
            "ScalingGroup.by_group",
        )
        sgroups = await loader.load(self.id)
        return [sg.name for sg in sgroups]

    async def resolve_user_nodes(
        self,
        info: graphene.ResolveInfo,
        filter: str | None = None,
        order: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult:
        from .user import UserRow

        graph_ctx: GraphQueryContext = info.context
        (
            query,
            conditions,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            UserRow,
            UserRow.uuid,
            filter,
            order,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        j = sa.join(UserRow, AssocProjectUserRow)
        user_query = query.select_from(j).where(AssocProjectUserRow.project_id == self.id)
        cnt_query = (
            sa.select(sa.func.count())
            .select_from(j)
            .where(AssocProjectUserRow.project_id == self.id)
        )
        for cond in conditions:
            cnt_query = cnt_query.where(cond)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            user_rows = (await db_session.scalars(user_query)).all()
            result = [UserNode.from_row(row) for row in user_rows]

            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id) -> ProjectNode:
        graph_ctx: GraphQueryContext = info.context
        _, project_id = AsyncNode.resolve_global_id(info, id)
        query = sa.select(ProjectRow).where(ProjectRow.id == project_id)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            project_row = (await db_session.scalars(query)).first()
            return cls.from_row(project_row)

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        filter_expr: str | None = None,
        order_expr: str | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
        before: str | None = None,
        last: int | None = None,
    ) -> ConnectionResolverResult:
        graph_ctx: GraphQueryContext = info.context
        (
            query,
            conditions,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            ProjectRow,
            ProjectRow.id,
            filter_expr,
            order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        cnt_query = sa.select(sa.func.count()).select_from(ProjectRow)
        for cond in conditions:
            cnt_query = cnt_query.where(cond)
        async with graph_ctx.db.begin_readonly_session() as db_session:
            project_rows = (await db_session.scalars(query)).all()
            result = [cls.from_row(row) for row in project_rows]

            total_cnt = await db_session.scalar(cnt_query)
            return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class ProjectConnection(Connection):
    class Meta:
        node = ProjectNode


class ProjectDotfile(TypedDict):
    data: str
    path: str
    perm: str


async def query_project_dotfiles(
    db_conn: SAConnection,
    project_id: Union[GUID, uuid.UUID],
) -> tuple[list[ProjectDotfile], int]:
    query = (
        sa.select([projects.c.dotfiles]).select_from(projects).where(projects.c.id == project_id)
    )
    packed_dotfile = await db_conn.scalar(query)
    if packed_dotfile is None:
        return [], MAXIMUM_DOTFILE_SIZE
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


async def query_project_domain(
    db_conn: SAConnection,
    project_id: Union[GUID, uuid.UUID],
) -> str:
    query = (
        sa.select([projects.c.domain_name]).select_from(projects).where(projects.c.id == project_id)
    )
    domain = await db_conn.scalar(query)
    return domain


def verify_dotfile_name(dotfile: str) -> bool:
    if dotfile in RESERVED_DOTFILES:
        return False
    return True
