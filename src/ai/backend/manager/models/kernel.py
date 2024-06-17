from __future__ import annotations

import asyncio
import enum
import logging
import uuid
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypedDict,
    TypeVar,
)

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from dateutil.tz import tzfile, tzutc
from graphene.types.datetime import DateTime as GQLDateTime
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, noload, relationship, selectinload

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.docker import ImageRef
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AccessKey,
    BinarySize,
    ClusterMode,
    KernelId,
    RedisConnectionInfo,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
    VFolderMount,
)

from ..api.exceptions import (
    BackendError,
    KernelCreationFailed,
    KernelDestructionFailed,
    KernelExecutionFailed,
    KernelRestartFailed,
    SessionNotFound,
)
from ..defs import DEFAULT_ROLE
from ..exceptions import AgentError
from .base import (
    GUID,
    Base,
    BigInt,
    EnumType,
    Item,
    KernelIDColumn,
    PaginatedList,
    ResourceSlotColumn,
    SessionIDColumnType,
    StructuredJSONObjectListColumn,
    URLColumn,
    batch_multiresult,
    batch_result,
    mapper_registry,
)
from .group import groups
from .image import ImageNode, ImageRow
from .minilang import JSONFieldItem
from .minilang.ordering import ColumnMapType, QueryOrderParser
from .minilang.queryfilter import FieldSpecType, QueryFilterParser, enum_field_getter
from .user import users
from .utils import ExtendedAsyncSAEngine, execute_with_retry, sql_json_merge

if TYPE_CHECKING:
    from .gql import GraphQueryContext

__all__ = (
    "get_user_email",
    "handle_kernel_exception",
    "kernels",
    "KernelRow",
    "KERNEL_STATUS_TRANSITION_MAP",
    "KernelStatistics",
    "KernelStatus",
    "KernelRole",
    "ComputeContainer",
    "ComputeContainerList",
    "LegacyComputeSession",
    "LegacyComputeSessionList",
    "AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES",
    "USER_RESOURCE_OCCUPYING_KERNEL_STATUSES",
    "RESOURCE_USAGE_KERNEL_STATUSES",
    "DEAD_KERNEL_STATUSES",
    "LIVE_STATUS",
    "PRIVATE_KERNEL_ROLES",
    "recalc_concurrency_used",
)

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models.kernel"))


class KernelStatus(enum.Enum):
    # values are only meaningful inside the manager
    PENDING = 0
    # ---
    SCHEDULED = 5
    # PENDING and SCHEDULED are not necessary anymore
    PREPARING = 10
    # ---
    BUILDING = 20
    PULLING = 21
    # ---
    RUNNING = 30
    RESTARTING = 31
    RESIZING = 32
    SUSPENDED = 33
    # ---
    TERMINATING = 40
    TERMINATED = 41
    ERROR = 42
    CANCELLED = 43


class KernelRole(enum.Enum):
    INFERENCE = "INFERENCE"
    COMPUTE = "COMPUTE"
    SYSTEM = "SYSTEM"


PRIVATE_KERNEL_ROLES = (KernelRole.SYSTEM,)


# statuses to consider when calculating current resource usage
AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES = tuple(
    e
    for e in KernelStatus
    if e
    not in (
        KernelStatus.TERMINATED,
        KernelStatus.PENDING,
        KernelStatus.CANCELLED,
    )
)

USER_RESOURCE_OCCUPYING_KERNEL_STATUSES = tuple(
    e
    for e in KernelStatus
    if e
    not in (
        KernelStatus.TERMINATING,
        KernelStatus.TERMINATED,
        KernelStatus.PENDING,
        KernelStatus.CANCELLED,
    )
)

# statuses to consider when calculating historical resource usage
RESOURCE_USAGE_KERNEL_STATUSES = (
    KernelStatus.TERMINATED,
    KernelStatus.RUNNING,
)

DEAD_KERNEL_STATUSES = (
    KernelStatus.CANCELLED,
    KernelStatus.TERMINATED,
)

LIVE_STATUS = (KernelStatus.RUNNING,)


OP_EXC = {
    "create_session": KernelCreationFailed,
    "restart_session": KernelRestartFailed,
    "destroy_session": KernelDestructionFailed,
    "execute": KernelExecutionFailed,
    "shutdown_service": KernelExecutionFailed,
    "upload_file": KernelExecutionFailed,
    "download_file": KernelExecutionFailed,
    "download_single": KernelExecutionFailed,
    "list_files": KernelExecutionFailed,
    "get_logs_from_agent": KernelExecutionFailed,
    "refresh_session": KernelExecutionFailed,
    "commit_session": KernelExecutionFailed,
}


async def get_user_email(
    db_session: SASession,
    kernel: KernelRow,
) -> str:
    query = sa.select([users.c.email]).select_from(users).where(users.c.uuid == kernel["user_uuid"])
    result = await db_session.execute(query)
    user_email = str(result.scalar())
    user_email = user_email.replace("@", "_")
    return user_email


def default_hostname(context) -> str:
    params = context.get_current_parameters()
    return f"{params['cluster_role']}{params['cluster_idx']}"


KERNEL_STATUS_TRANSITION_MAP: Mapping[KernelStatus, set[KernelStatus]] = {
    KernelStatus.PENDING: {
        s for s in KernelStatus if s not in (KernelStatus.PENDING, KernelStatus.TERMINATED)
    },
    KernelStatus.SCHEDULED: {
        s
        for s in KernelStatus
        if s
        not in (
            KernelStatus.SCHEDULED,
            KernelStatus.PENDING,
            KernelStatus.TERMINATED,
        )
    },
    KernelStatus.PREPARING: {
        s
        for s in KernelStatus
        if s
        not in (
            KernelStatus.PREPARING,
            KernelStatus.PENDING,
            KernelStatus.SCHEDULED,
            KernelStatus.TERMINATED,
        )
    },
    KernelStatus.BUILDING: {
        s
        for s in KernelStatus
        if s
        not in (
            KernelStatus.BUILDING,
            KernelStatus.PENDING,
            KernelStatus.SCHEDULED,
            KernelStatus.TERMINATED,
        )
    },
    KernelStatus.PULLING: {
        s
        for s in KernelStatus
        if s
        not in (
            KernelStatus.PULLING,
            KernelStatus.PENDING,
            KernelStatus.SCHEDULED,
            KernelStatus.TERMINATED,
        )
    },
    KernelStatus.RUNNING: {
        KernelStatus.RESTARTING,
        KernelStatus.RESIZING,
        KernelStatus.TERMINATING,
        KernelStatus.TERMINATED,
        KernelStatus.ERROR,
    },
    KernelStatus.RESTARTING: {
        s
        for s in KernelStatus
        if s
        not in (
            KernelStatus.RESTARTING,
            KernelStatus.PENDING,
            KernelStatus.SCHEDULED,
            KernelStatus.TERMINATED,
        )
    },
    KernelStatus.RESIZING: {
        s
        for s in KernelStatus
        if s
        not in (
            KernelStatus.RESIZING,
            KernelStatus.PENDING,
            KernelStatus.SCHEDULED,
            KernelStatus.TERMINATED,
        )
    },
    KernelStatus.SUSPENDED: {
        s
        for s in KernelStatus
        if s
        not in (
            KernelStatus.SUSPENDED,
            KernelStatus.PENDING,
            KernelStatus.SCHEDULED,
            KernelStatus.TERMINATED,
        )
    },
    KernelStatus.TERMINATING: {KernelStatus.TERMINATED, KernelStatus.ERROR},
    KernelStatus.TERMINATED: set(),
    KernelStatus.ERROR: set(),
    KernelStatus.CANCELLED: set(),
}


@actxmgr
async def handle_kernel_exception(
    db: ExtendedAsyncSAEngine,
    op: str,
    kernel_id: KernelId,
    error_callback=None,
    cancellation_callback=None,
    set_error: bool = False,
) -> AsyncIterator[None]:
    exc_class = OP_EXC[op]
    # NOTE: Error logging is done outside of this actxmanager.
    try:
        yield
    except asyncio.TimeoutError:
        if set_error:
            await KernelRow.set_kernel_status(
                db,
                kernel_id,
                KernelStatus.ERROR,
                reason=f"operation-timeout ({op})",
            )
        if error_callback:
            await error_callback()
        raise exc_class("TIMEOUT") from None
    except asyncio.CancelledError:
        if cancellation_callback:
            await cancellation_callback()
        raise
    except AgentError as e:
        if set_error:
            await KernelRow.set_kernel_status(
                db,
                kernel_id,
                KernelStatus.ERROR,
                reason=f"agent-error ({e!r})",
                status_data={
                    "error": {
                        "src": "agent",
                        "agent_id": e.agent_id,
                        "name": e.exc_name,
                        "repr": e.exc_repr,
                    },
                },
            )
        if error_callback:
            await error_callback()
        raise exc_class("FAILURE", e) from None
    except BackendError:
        # silently re-raise to make them handled by gateway http handlers
        raise
    except Exception as e:
        if set_error:
            await KernelRow.set_kernel_status(
                db,
                kernel_id,
                KernelStatus.ERROR,
                reason=f"other-error ({e!r})",
                status_data={
                    "error": {
                        "src": "other",
                        "name": e.__class__.__name__,
                        "repr": repr(e),
                    },
                },
            )
        if error_callback:
            await error_callback()
        raise


kernels = sa.Table(
    "kernels",
    mapper_registry.metadata,
    # The Backend.AI-side UUID for each kernel
    # (mapped to a container in the docker backend and a pod in the k8s backend)
    KernelIDColumn(),
    # session_id == id when the kernel is the main container in a multi-container session or a
    # single-container session.
    # Otherwise, it refers the kernel ID of the main container of the belonged multi-container session.
    sa.Column(
        "session_id",
        SessionIDColumnType,
        sa.ForeignKey("sessions.id"),
        unique=False,
        index=True,
        nullable=False,
    ),
    sa.Column("session_creation_id", sa.String(length=32), unique=False, index=False),
    sa.Column("session_name", sa.String(length=64), unique=False, index=True),  # previously sess_id
    sa.Column(
        "session_type",
        EnumType(SessionTypes),
        index=True,
        nullable=False,  # previously sess_type
        default=SessionTypes.INTERACTIVE,
        server_default=SessionTypes.INTERACTIVE.name,
    ),
    sa.Column(
        "cluster_mode",
        sa.String(length=16),
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE.name,
    ),
    sa.Column("cluster_size", sa.Integer, nullable=False, default=1),
    sa.Column(
        "cluster_role", sa.String(length=16), nullable=False, default=DEFAULT_ROLE, index=True
    ),
    sa.Column("cluster_idx", sa.Integer, nullable=False, default=0),
    sa.Column("local_rank", sa.Integer, nullable=False, default=0),
    sa.Column("cluster_hostname", sa.String(length=64), nullable=False, default=default_hostname),
    # Resource ownership
    sa.Column("scaling_group", sa.ForeignKey("scaling_groups.name"), index=True, nullable=True),
    sa.Column("agent", sa.String(length=64), sa.ForeignKey("agents.id"), nullable=True),
    sa.Column("agent_addr", sa.String(length=128), nullable=True),
    sa.Column("domain_name", sa.String(length=64), sa.ForeignKey("domains.name"), nullable=False),
    sa.Column("group_id", GUID, sa.ForeignKey("groups.id"), nullable=False),
    sa.Column("user_uuid", GUID, sa.ForeignKey("users.uuid"), nullable=False),
    sa.Column("access_key", sa.String(length=20), sa.ForeignKey("keypairs.access_key")),
    # `image` is a string shaped "<REGISTRY>/<IMAGE>:<TAG>". it is identical to images.name column
    sa.Column("image", sa.String(length=512)),
    # ForeignKeyIDColumn("image_id", "images.id"),
    sa.Column("architecture", sa.String(length=32), default="x86_64"),
    sa.Column("registry", sa.String(length=512)),
    sa.Column("tag", sa.String(length=64), nullable=True),
    # Resource occupation
    sa.Column("container_id", sa.String(length=64)),
    sa.Column("occupied_slots", ResourceSlotColumn(), nullable=False),
    sa.Column("requested_slots", ResourceSlotColumn(), nullable=False, default=ResourceSlot()),
    sa.Column("occupied_shares", pgsql.JSONB(), nullable=False, default={}),  # legacy
    sa.Column("environ", sa.ARRAY(sa.String), nullable=True),
    sa.Column("mounts", sa.ARRAY(sa.String), nullable=True),  # list of list; legacy since 22.03
    sa.Column("mount_map", pgsql.JSONB(), nullable=True, default={}),  # legacy since 22.03
    sa.Column("vfolder_mounts", StructuredJSONObjectListColumn(VFolderMount), nullable=True),
    sa.Column("attached_devices", pgsql.JSONB(), nullable=True, default={}),
    sa.Column("resource_opts", pgsql.JSONB(), nullable=True, default={}),
    sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True),
    # Port mappings
    # If kernel_host is NULL, it is assumed to be same to the agent host or IP.
    sa.Column("kernel_host", sa.String(length=128), nullable=True),
    sa.Column("repl_in_port", sa.Integer(), nullable=False),
    sa.Column("repl_out_port", sa.Integer(), nullable=False),
    sa.Column("stdin_port", sa.Integer(), nullable=False),  # legacy for stream_pty
    sa.Column("stdout_port", sa.Integer(), nullable=False),  # legacy for stream_pty
    sa.Column("service_ports", pgsql.JSONB(), nullable=True),
    sa.Column("preopen_ports", sa.ARRAY(sa.Integer), nullable=True),
    sa.Column("use_host_network", sa.Boolean(), default=False, nullable=False),
    # Lifecycle
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    sa.Column(
        "terminated_at", sa.DateTime(timezone=True), nullable=True, default=sa.null(), index=True
    ),
    sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True, default=sa.null()),
    sa.Column(
        "status",
        EnumType(KernelStatus),
        default=KernelStatus.PENDING,
        server_default=KernelStatus.PENDING.name,
        nullable=False,
        index=True,
    ),
    sa.Column(
        "role",
        EnumType(KernelRole),
        default=KernelRole.COMPUTE,
        server_default=KernelRole.COMPUTE.name,
        nullable=False,
        index=True,
    ),
    sa.Column("status_changed", sa.DateTime(timezone=True), nullable=True, index=True),
    sa.Column("status_info", sa.Unicode(), nullable=True, default=sa.null()),
    # status_info contains a kebab-cased string that expresses a summary of the last status change.
    # Examples: "user-requested", "self-terminated", "predicate-checks-failed", "no-available-instances"
    sa.Column("status_data", pgsql.JSONB(), nullable=True, default=sa.null()),
    # status_data contains a JSON object that contains detailed data for the last status change.
    # During scheduling (as PENDING + ("no-available-instances" | "predicate-checks-failed")):
    # {
    #   "scheduler": {
    #     // shceudler attempt information
    #     // NOTE: the whole field may be NULL before the first attempt!
    #     "retries": 5,
    #         // the number of scheudling attempts (used to avoid HoL blocking as well)
    #     "last_try": "2021-05-01T12:34:56.123456+09:00",
    #         // an ISO 8601 formatted timestamp of the last attempt
    #     "failed_predicates": [
    #       { "name": "concurrency", "msg": "You cannot run more than 30 concurrent sessions." },
    #           // see the manager.scheduler.predicates module for possible messages
    #       ...
    #     ],
    #     "passed_predicates": [ {"name": "reserved_time"}, ... ],  // names only
    #   }
    # }
    #
    # While running: the field is NULL.
    #
    # After termination:
    # {
    #   "kernel": {
    #     // termination info for the individual kernel
    #     "exit_code": 123,
    #         // maybe null during termination
    #   },
    #   "session": {
    #     // termination info for the session
    #     "status": "terminating" | "terminated"
    #         // "terminated" means all kernels that belong to the same session has terminated.
    #         // used to prevent duplication of SessionTerminatedEvent
    #   }
    # }
    sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null()),
    sa.Column("callback_url", URLColumn, nullable=True, default=sa.null()),
    sa.Column("startup_command", sa.Text, nullable=True),
    sa.Column(
        "result",
        EnumType(SessionResult),
        default=SessionResult.UNDEFINED,
        server_default=SessionResult.UNDEFINED.name,
        nullable=False,
        index=True,
    ),
    sa.Column("internal_data", pgsql.JSONB(), nullable=True),
    sa.Column("container_log", sa.LargeBinary(), nullable=True),
    # Resource metrics measured upon termination
    sa.Column("num_queries", sa.BigInteger(), default=0),
    sa.Column("last_stat", pgsql.JSONB(), nullable=True, default=sa.null()),
    sa.Index("ix_kernels_sess_id_role", "session_id", "cluster_role", unique=False),
    sa.Index("ix_kernels_status_role", "status", "cluster_role"),
    sa.Index(
        "ix_kernels_updated_order",
        sa.func.greatest("created_at", "terminated_at", "status_changed"),
        unique=False,
    ),
    sa.Index(
        "ix_kernels_unique_sess_token",
        "access_key",
        "session_name",
        unique=True,
        postgresql_where=sa.text(
            "status NOT IN ('TERMINATED', 'CANCELLED') and cluster_role = 'main'"
        ),
    ),
)


class KernelRow(Base):
    __table__ = kernels
    session = relationship("SessionRow", back_populates="kernels")
    image_row = relationship(
        "ImageRow",
        foreign_keys="KernelRow.image",
        primaryjoin="KernelRow.image == ImageRow.name",
    )
    agent_row = relationship("AgentRow", back_populates="kernels")
    group_row = relationship("GroupRow", back_populates="kernels")
    user_row = relationship("UserRow", back_populates="kernels")

    @property
    def image_ref(self) -> ImageRef:
        return ImageRef(self.image, [self.registry], self.architecture)

    @property
    def cluster_name(self) -> str:
        if self.cluster_role == DEFAULT_ROLE:
            return self.cluster_role
        return self.cluster_role + str(self.cluster_idx)

    @property
    def used_time(self) -> Optional[str]:
        if self.terminated_at is not None:
            return str(self.terminated_at - self.created_at)
        return None

    def get_used_days(self, local_tz: tzfile) -> Optional[int]:
        if self.terminated_at is not None:
            return (
                self.terminated_at.astimezone(local_tz).toordinal()
                - self.created_at.astimezone(local_tz).toordinal()
                + 1
            )
        return None

    @property
    def is_private(self) -> bool:
        return self.role in PRIVATE_KERNEL_ROLES

    @staticmethod
    async def get_kernel(
        db: ExtendedAsyncSAEngine, kern_id: uuid.UUID, allow_stale: bool = False
    ) -> KernelRow:
        from .agent import AgentStatus

        async def _query():
            async with db.begin_readonly_session() as db_sess:
                query = (
                    sa.select(KernelRow)
                    .where(KernelRow.id == kern_id)
                    .options(
                        noload("*"),
                        selectinload(KernelRow.agent_row).options(noload("*")),
                    )
                )
                result = (await db_sess.execute(query)).scalars().all()

                cand = result
                if not allow_stale:
                    cand = [
                        k
                        for k in result
                        if (k.status not in DEAD_KERNEL_STATUSES)
                        and (k.agent_row.status == AgentStatus.ALIVE)
                    ]
                if not cand:
                    raise SessionNotFound
                return cand[0]

        return await execute_with_retry(_query)

    @classmethod
    async def set_kernel_status(
        cls,
        db: ExtendedAsyncSAEngine,
        kernel_id: KernelId,
        status: KernelStatus,
        *,
        status_data: Optional[Mapping[str, Any]] = None,
        reason: Optional[str] = None,
        status_changed_at: Optional[datetime] = None,
    ) -> None:
        assert (
            status != KernelStatus.TERMINATED
        ), "TERMINATED status update must be handled in mark_kernel_terminated()"
        if status_changed_at is None:
            now = datetime.now(tzutc())
        else:
            now = status_changed_at
        data = {
            "status": status,
            "status_changed": now,
            "status_history": sql_json_merge(
                kernels.c.status_history,
                (),
                {
                    status.name: now.isoformat(),  # ["PULLING", "PREPARING"]
                },
            ),
        }
        if status_data is not None:
            data["status_data"] = status_data
        if reason is not None:
            data["status_info"] = reason
        if status in (KernelStatus.CANCELLED, KernelStatus.TERMINATED):
            data["terminated_at"] = now

        await cls.update_kernel(db, kernel_id, status, update_data=data)

    @classmethod
    async def update_kernel(
        cls,
        db: ExtendedAsyncSAEngine,
        kernel_id: KernelId,
        new_status: KernelStatus,
        update_data: Optional[Mapping[str, Any]] = None,
    ) -> bool:
        """
        Update kernel by given id and data.
        Return True if the kernel is updated, else return False.
        """

        now = datetime.now(tzutc())

        async def _update() -> bool:
            async with db.begin_session() as db_session:
                kernel_query = (
                    sa.select(KernelRow)
                    .where(KernelRow.id == kernel_id)
                    .with_for_update()
                    .options(
                        noload("*"),
                        load_only(KernelRow.status, KernelRow.session_id),
                    )
                )
                kernel_row = (await db_session.scalars(kernel_query)).first()

                if new_status not in KERNEL_STATUS_TRANSITION_MAP[kernel_row.status]:
                    # TODO: log or raise error
                    return False
                if update_data is None:
                    update_values = {
                        "status": new_status,
                        "status_history": sql_json_merge(
                            KernelRow.status_history,
                            (),
                            {
                                new_status.name: now.isoformat(),
                            },
                        ),
                    }
                else:
                    update_values = {
                        **update_data,
                        "status": new_status,
                    }

                update_query = (
                    sa.update(KernelRow).where(KernelRow.id == kernel_id).values(**update_values)
                )
                await db_session.execute(update_query)
            return True

        return await execute_with_retry(_update)


DEFAULT_KERNEL_ORDERING = [
    sa.desc(
        sa.func.greatest(
            KernelRow.created_at,
            KernelRow.terminated_at,
            KernelRow.status_changed,
        )
    ),
]


class SessionInfo(TypedDict):
    session_id: SessionId
    session_name: str
    status: KernelStatus
    created_at: datetime


class KernelStatistics:
    @classmethod
    async def batch_load_by_kernel(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        async def _build_pipeline(redis: Redis) -> Pipeline:
            pipe = redis.pipeline()
            for sess_id in session_ids:
                await pipe.get(str(sess_id))
            return pipe

        stats = []
        results = await redis_helper.execute(ctx.redis_stat, _build_pipeline)
        for result in results:
            if result is not None:
                stats.append(msgpack.unpackb(result))
            else:
                stats.append(None)
        return stats

    @classmethod
    async def batch_load_inference_metrics_by_kernel(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        async def _build_pipeline(redis: Redis) -> Pipeline:
            pipe = redis.pipeline()
            for sess_id in session_ids:
                await pipe.mget([
                    f"session.{sess_id}.requests",
                    f"session.{sess_id}.last_response_time",
                ])
            return pipe

        stats = []
        results = await redis_helper.execute(ctx.redis_live, _build_pipeline)
        for result in results:
            if result[0] is not None and result[1] is not None:
                requests = int(result[0])
                last_response_ms = int(result[1])
            else:
                requests = 0
                last_response_ms = 0
            stats.append({"requests": int(requests), "last_response_ms": last_response_ms})

        return stats


class ComputeContainer(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    # identity
    idx = graphene.Int()  # legacy
    role = graphene.String()  # legacy
    hostname = graphene.String()  # legacy
    kernel_id = graphene.UUID(description="Added in 24.03.1.")
    cluster_idx = graphene.Int()
    local_rank = graphene.Int()
    cluster_role = graphene.String()
    cluster_hostname = graphene.String()
    session_id = graphene.UUID()  # owner session

    # image
    image = graphene.String(description="Deprecated since 24.03.0; use image_object.name")
    image_object = graphene.Field(ImageNode, description="Added in 24.03.0.")
    architecture = graphene.String()
    registry = graphene.String()

    # status
    status = graphene.String()
    status_changed = GQLDateTime()
    status_info = graphene.String()
    status_data = graphene.JSONString()
    created_at = GQLDateTime()
    terminated_at = GQLDateTime()
    starts_at = GQLDateTime()
    scheduled_at = GQLDateTime()
    abusing_report = graphene.JSONString()

    # resources
    agent = graphene.String()
    agent_addr = graphene.String()
    container_id = graphene.String()
    resource_opts = graphene.JSONString()
    occupied_slots = graphene.JSONString()
    live_stat = graphene.JSONString()
    last_stat = graphene.JSONString()
    preopen_ports = graphene.List(lambda: graphene.Int, required=False)

    @classmethod
    def parse_row(cls, ctx: GraphQueryContext, row: KernelRow) -> Mapping[str, Any]:
        assert row is not None
        from .user import UserRole

        is_superadmin = ctx.user["role"] == UserRole.SUPERADMIN
        if is_superadmin:
            hide_agents = False
        else:
            hide_agents = ctx.local_config["manager"]["hide-agents"]
        status_history = row.status_history or {}
        return {
            # identity
            "id": row.id,
            "kernel_id": row.id,
            "idx": row.cluster_idx,
            "role": row.cluster_role,
            "hostname": row.cluster_hostname,
            "cluster_idx": row.cluster_idx,
            "local_rank": row.local_rank,
            "cluster_role": row.cluster_role,
            "cluster_hostname": row.cluster_hostname,
            "session_id": row.session_id,
            # image
            "image": row.image,
            "image_object": ImageNode.from_row(row.image_row),
            "architecture": row.architecture,
            "registry": row.registry,
            # status
            "status": row.status.name,
            "status_changed": row.status_changed,
            "status_info": row.status_info,
            "status_data": row.status_data,
            "created_at": row.created_at,
            "terminated_at": row.terminated_at,
            "starts_at": row.starts_at,
            "scheduled_at": status_history.get(KernelStatus.SCHEDULED.name),
            "occupied_slots": row.occupied_slots.to_json(),
            # resources
            "agent": row.agent if not hide_agents else None,
            "agent_addr": row.agent_addr if not hide_agents else None,
            "container_id": row.container_id if not hide_agents else None,
            "resource_opts": row.resource_opts,
            "preopen_ports": row.preopen_ports,
            # statistics
            # last_stat is resolved by Graphene (resolve_last_stat method)
        }

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[ComputeContainer]:
        if row is None:
            return None
        props = cls.parse_row(ctx, row)
        return cls(**props)

    # last_stat also fetches data from Redis, meaning that
    # both live_stat and last_stat will reference same data from same source
    # we can leave last_stat value for legacy support, as an alias to last_stat
    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "KernelStatistics.by_kernel")
        return await loader.load(self.id)

    async def resolve_last_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        return await self.resolve_live_stat(info)

    async def resolve_abusing_report(
        self,
        info: graphene.ResolveInfo,
        access_key: AccessKey | None,
    ) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        if access_key is None:
            return None
        return await graph_ctx.registry.get_abusing_report(self.id)

    _queryfilter_fieldspec: FieldSpecType = {
        "image": ("image", None),
        "architecture": ("architecture", None),
        "agent": ("agent", None),
        "agent_addr": ("agent_addr", None),
        "cluster_idx": ("cluster_idx", None),
        "local_rank": ("local_rank", None),
        "cluster_role": ("cluster_role", None),
        "cluster_hostname": ("cluster_hostname", None),
        "status": ("status", enum_field_getter(KernelStatus)),
        "status_info": ("status_info", None),
        "created_at": ("created_at", dtparse),
        "status_changed": ("status_changed", dtparse),
        "terminated_at": ("terminated_at", dtparse),
        "scheduled_at": (JSONFieldItem("status_history", KernelStatus.SCHEDULED.name), dtparse),
    }

    _queryorder_colmap: ColumnMapType = {
        "image": ("image", None),
        "architecture": ("architecture", None),
        "agent": ("agent", None),
        "agent_addr": ("agent_addr", None),
        "cluster_idx": ("cluster_idx", None),
        "local_rank": ("local_rank", None),
        "cluster_role": ("cluster_role", None),
        "cluster_hostname": ("cluster_hostname", None),
        "status": ("status", None),
        "status_info": ("status_info", None),
        "status_changed": ("status_info", None),
        "created_at": ("created_at", None),
        "terminated_at": ("terminated_at", None),
        "scheduled_at": (JSONFieldItem("status_history", KernelStatus.SCHEDULED.name), None),
    }

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        session_id: SessionId,
        *,
        cluster_role: str = None,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        access_key: str = None,
        filter: str = None,
    ) -> int:
        query = (
            sa.select([sa.func.count()])
            .select_from(KernelRow)
            .where(KernelRow.session_id == session_id)
        )
        if cluster_role is not None:
            query = query.where(KernelRow.cluster_role == cluster_role)
        if domain_name is not None:
            query = query.where(KernelRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(KernelRow.group_id == group_id)
        if access_key is not None:
            query = query.where(KernelRow.access_key == access_key)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with ctx.db.begin_readonly_session() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        session_id: SessionId,
        *,
        cluster_role: str = None,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        access_key: AccessKey = None,
        filter: str = None,
        order: str = None,
    ) -> Sequence[Optional[ComputeContainer]]:
        query = (
            sa.select(KernelRow)
            .where(KernelRow.session_id == session_id)
            .limit(limit)
            .offset(offset)
            .options(selectinload(KernelRow.image_row).options(selectinload(ImageRow.aliases)))
        )
        if cluster_role is not None:
            query = query.where(KernelRow.cluster_role == cluster_role)
        if domain_name is not None:
            query = query.where(KernelRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(KernelRow.group_id == group_id)
        if access_key is not None:
            query = query.where(KernelRow.access_key == access_key)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(*DEFAULT_KERNEL_ORDERING)
        async with ctx.db.begin_readonly_session() as db_session:
            return [cls.from_row(ctx, r) async for r in (await db_session.stream_scalars(query))]

    @classmethod
    async def batch_load_by_session(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Sequence[ComputeContainer]]:
        query = (
            sa.select(KernelRow)
            # TODO: use "owner session ID" when we implement multi-container session
            .where(KernelRow.session_id.in_(session_ids))
            .options(selectinload(KernelRow.image_row).options(selectinload(ImageRow.aliases)))
        )
        async with ctx.db.begin_readonly_session() as conn:
            return await batch_multiresult(
                ctx,
                conn,
                query,
                cls,
                session_ids,
                lambda row: row.session_id,
            )

    @classmethod
    async def batch_load_detail(
        cls,
        ctx: GraphQueryContext,
        container_ids: Sequence[KernelId],
        *,
        domain_name: str = None,
        access_key: AccessKey = None,
    ) -> Sequence[Optional[ComputeContainer]]:
        query = (
            sa.select(KernelRow)
            .where(
                (KernelRow.id.in_(container_ids)),
            )
            .options(selectinload(KernelRow.group_row))
            .options(selectinload(KernelRow.user_row))
            .options(selectinload(KernelRow.image_row))
        )
        if domain_name is not None:
            query = query.where(KernelRow.domain_name == domain_name)
        if access_key is not None:
            query = query.where(KernelRow.access_key == access_key)
        async with ctx.db.begin_readonly_session() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                container_ids,
                lambda row: row.id,
            )


class ComputeContainerList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(ComputeContainer, required=True)


# --------- pre-v5 legacy -----------

MetricValueType = TypeVar("MetricValueType", int, float)


class LegacyComputeSession(graphene.ObjectType):
    """
    Represents a main session.
    """

    class Meta:
        interfaces = (Item,)

    tag = graphene.String()  # Only for ComputeSession
    sess_id = graphene.String()  # legacy
    sess_type = graphene.String()  # legacy
    session_name = graphene.String()
    session_type = graphene.String()
    role = graphene.String()
    image = graphene.String()
    architecture = graphene.String()
    registry = graphene.String()
    domain_name = graphene.String()
    group_name = graphene.String()
    group_id = graphene.UUID()
    scaling_group = graphene.String()
    user_uuid = graphene.UUID()
    access_key = graphene.String()

    status = graphene.String()
    status_changed = GQLDateTime()
    status_info = graphene.String()
    created_at = GQLDateTime()
    terminated_at = GQLDateTime()
    startup_command = graphene.String()
    result = graphene.String()

    # hidable fields by configuration
    agent = graphene.String()
    container_id = graphene.String()

    service_ports = graphene.JSONString()

    occupied_slots = graphene.JSONString()
    occupied_shares = graphene.JSONString()
    mounts = graphene.List(lambda: graphene.List(lambda: graphene.String))
    resource_opts = graphene.JSONString()

    num_queries = BigInt()
    live_stat = graphene.JSONString()
    last_stat = graphene.JSONString()

    user_email = graphene.String()

    # Legacy fields
    lang = graphene.String()
    mem_slot = graphene.Int()
    cpu_slot = graphene.Float()
    gpu_slot = graphene.Float()
    tpu_slot = graphene.Float()
    cpu_used = BigInt()
    cpu_using = graphene.Float()
    mem_max_bytes = BigInt()
    mem_cur_bytes = BigInt()
    net_rx_bytes = BigInt()
    net_tx_bytes = BigInt()
    io_read_bytes = BigInt()
    io_write_bytes = BigInt()
    io_max_scratch_size = BigInt()
    io_cur_scratch_size = BigInt()

    # last_stat also fetches data from Redis, meaning that
    # both live_stat and last_stat will reference same data from same source
    # we can leave last_stat value for legacy support, as an alias to last_stat
    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "KernelStatistics.by_kernel")
        return await loader.load(self.id)

    async def resolve_last_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        return await self.resolve_live_stat(info)

    async def _resolve_legacy_metric(
        self,
        info: graphene.ResolveInfo,
        metric_key: str,
        metric_field: str,
        convert_type: Type[MetricValueType],
    ) -> Optional[MetricValueType]:
        if not hasattr(self, "status"):
            return None
        graph_ctx: GraphQueryContext = info.context
        if KernelStatus[self.status] not in LIVE_STATUS:
            if self.last_stat is None:
                return convert_type(0)
            metric = self.last_stat.get(metric_key)
            if metric is None:
                return convert_type(0)
            value = metric.get(metric_field)
            if value is None:
                return convert_type(0)
            return convert_type(value)
        else:
            loader = graph_ctx.dataloader_manager.get_loader(
                graph_ctx, "KernelStatistics.by_kernel"
            )
            kstat = await loader.load(self.id)
            if kstat is None:
                return convert_type(0)
            metric = kstat.get(metric_key)
            if metric is None:
                return convert_type(0)
            value = metric.get(metric_field)
            if value is None:
                return convert_type(0)
            return convert_type(value)

    async def resolve_cpu_used(self, info: graphene.ResolveInfo) -> Optional[float]:
        return await self._resolve_legacy_metric(info, "cpu_used", "current", float)

    async def resolve_cpu_using(self, info: graphene.ResolveInfo) -> Optional[float]:
        return await self._resolve_legacy_metric(info, "cpu_util", "pct", float)

    async def resolve_mem_max_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "mem", "stats.max", int)

    async def resolve_mem_cur_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "mem", "current", int)

    async def resolve_net_rx_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "net_rx", "stats.rate", int)

    async def resolve_net_tx_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "net_tx", "stats.rate", int)

    async def resolve_io_read_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "io_read", "current", int)

    async def resolve_io_write_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "io_write", "current", int)

    async def resolve_io_max_scratch_size(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "io_scratch_size", "stats.max", int)

    async def resolve_io_cur_scratch_size(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "io_scratch_size", "current", int)

    @classmethod
    def parse_row(cls, ctx: GraphQueryContext, row: Row) -> Mapping[str, Any]:
        assert row is not None
        from .user import UserRole

        mega = 2**20
        is_superadmin = ctx.user["role"] == UserRole.SUPERADMIN
        if is_superadmin:
            hide_agents = False
        else:
            hide_agents = ctx.local_config["manager"]["hide-agents"]
        return {
            "id": row["id"],
            "sess_id": row["session_name"],  # legacy, will be deprecated
            "sess_type": row["session_type"].name,  # legacy, will be deprecated
            "session_name": row["session_name"],
            "session_type": row["session_type"].name,
            "role": row["cluster_role"],
            "tag": row["tag"],
            "image": row["image"],
            "architecture": row["architecture"],
            "registry": row["registry"],
            "domain_name": row["domain_name"],
            "group_name": row[
                "name"
            ],  # group.name (group is omitted since use_labels=True is not used)
            "group_id": row["group_id"],
            "scaling_group": row["scaling_group"],
            "user_uuid": row["user_uuid"],
            "access_key": row["access_key"],
            "status": row["status"].name,
            "status_changed": row["status_changed"],
            "status_info": row["status_info"],
            "status_data": row["status_data"],
            "created_at": row["created_at"],
            "terminated_at": row["terminated_at"],
            "startup_command": row["startup_command"],
            "result": row["result"].name,
            "service_ports": row["service_ports"],
            "occupied_slots": row["occupied_slots"].to_json(),
            "vfolder_mounts": row["vfolder_mounts"],
            "resource_opts": row["resource_opts"],
            "num_queries": row["num_queries"],
            # optionally hidden
            "agent": row["agent"] if not hide_agents else None,
            "container_id": row["container_id"] if not hide_agents else None,
            # live_stat is resolved by Graphene
            # last_stat is resolved by Graphene
            "user_email": row["email"],
            # Legacy fields
            # NOTE: currently graphene always uses resolve methods!
            "cpu_used": 0,
            "mem_max_bytes": 0,
            "mem_cur_bytes": 0,
            "net_rx_bytes": 0,
            "net_tx_bytes": 0,
            "io_read_bytes": 0,
            "io_write_bytes": 0,
            "io_max_scratch_size": 0,
            "io_cur_scratch_size": 0,
            "lang": row["image"],
            "occupied_shares": row["occupied_shares"],
            "mem_slot": BinarySize.from_str(row["occupied_slots"].get("mem", 0)) // mega,
            "cpu_slot": float(row["occupied_slots"].get("cpu", 0)),
            "gpu_slot": float(row["occupied_slots"].get("cuda.device", 0)),
            "tpu_slot": float(row["occupied_slots"].get("tpu.device", 0)),
        }

    @classmethod
    def from_row(cls, context: GraphQueryContext, row: Row) -> Optional[LegacyComputeSession]:
        if row is None:
            return None
        props = cls.parse_row(context, row)
        return cls(**props)

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        access_key: AccessKey = None,
        status: str = None,
    ) -> int:
        if isinstance(status, str):
            status_list = [KernelStatus[s] for s in status.split(",")]
        elif isinstance(status, KernelStatus):
            status_list = [status]
        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(kernels.c.cluster_role == DEFAULT_ROLE)
        )
        if domain_name is not None:
            query = query.where(kernels.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(kernels.c.group_id == group_id)
        if access_key is not None:
            query = query.where(kernels.c.access_key == access_key)
        if status is not None:
            query = query.where(kernels.c.status.in_(status_list))
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        access_key: AccessKey = None,
        status: str = None,
        order_key: str = None,
        order_asc: bool = True,
    ) -> Sequence[LegacyComputeSession]:
        if isinstance(status, str):
            status_list = [KernelStatus[s] for s in status.split(",")]
        elif isinstance(status, KernelStatus):
            status_list = [status]
        if order_key is None:
            _ordering = DEFAULT_KERNEL_ORDERING
        else:
            _order_func = sa.asc if order_asc else sa.desc
            _ordering = [_order_func(getattr(kernels.c, order_key))]
        j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
            users, users.c.uuid == kernels.c.user_uuid
        )
        query = (
            sa.select([kernels, groups.c.name, users.c.email])
            .select_from(j)
            .where(kernels.c.cluster_role == DEFAULT_ROLE)
            .order_by(*_ordering)
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(kernels.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(kernels.c.group_id == group_id)
        if access_key is not None:
            query = query.where(kernels.c.access_key == access_key)
        if status is not None:
            query = query.where(kernels.c.status.in_(status_list))
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]

    @classmethod
    async def batch_load(
        cls,
        ctx: GraphQueryContext,
        access_keys: AccessKey,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        status: str = None,
    ) -> Sequence[Optional[LegacyComputeSession]]:
        j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
            users, users.c.uuid == kernels.c.user_uuid
        )
        query = (
            sa.select([kernels, groups.c.name, users.c.email])
            .select_from(j)
            .where(
                (kernels.c.access_key.in_(access_keys)) & (kernels.c.cluster_role == DEFAULT_ROLE),
            )
            .order_by(
                sa.desc(
                    sa.func.greatest(
                        kernels.c.created_at,
                        kernels.c.terminated_at,
                        kernels.c.status_changed,
                    )
                ),
            )
            .limit(100)
        )
        if domain_name is not None:
            query = query.where(kernels.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(kernels.c.group_id == group_id)
        if status is not None:
            query = query.where(kernels.c.status == status)
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                access_keys,
                lambda row: row["access_key"],
            )

    @classmethod
    async def batch_load_detail(
        cls,
        ctx: GraphQueryContext,
        sess_ids: Sequence[SessionId],
        *,
        domain_name: str = None,
        access_key: AccessKey = None,
        status: str = None,
    ) -> Sequence[Sequence[LegacyComputeSession]]:
        status_list = []
        if isinstance(status, str):
            status_list = [KernelStatus[s] for s in status.split(",")]
        elif isinstance(status, KernelStatus):
            status_list = [status]
        elif status is None:
            status_list = [KernelStatus["RUNNING"]]
        j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
            users, users.c.uuid == kernels.c.user_uuid
        )
        query = (
            sa.select([kernels, groups.c.name, users.c.email])
            .select_from(j)
            .where((kernels.c.cluster_role == DEFAULT_ROLE) & (kernels.c.session_id.in_(sess_ids)))
        )
        if domain_name is not None:
            query = query.where(kernels.c.domain_name == domain_name)
        if access_key is not None:
            query = query.where(kernels.c.access_key == access_key)
        if status_list:
            query = query.where(kernels.c.status.in_(status_list))
        async with ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                ctx,
                conn,
                query,
                cls,
                sess_ids,
                lambda row: row["session_name"],
            )


class LegacyComputeSessionList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(LegacyComputeSession, required=True)


async def recalc_concurrency_used(
    db_sess: SASession,
    redis_stat: RedisConnectionInfo,
    access_key: AccessKey,
) -> None:
    concurrency_used: int
    async with db_sess.begin_nested():
        result = await db_sess.execute(
            sa.select(sa.func.count())
            .select_from(KernelRow)
            .where(
                (KernelRow.access_key == access_key)
                & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                & (KernelRow.role.not_in(PRIVATE_KERNEL_ROLES)),
            ),
        )
        concurrency_used = result.scalar()
        result = await db_sess.execute(
            sa.select(sa.func.count())
            .select_from(KernelRow)
            .where(
                (KernelRow.access_key == access_key)
                & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                & (KernelRow.role.in_(PRIVATE_KERNEL_ROLES)),
            ),
        )
        sftp_concurrency_used = result.scalar()
        assert isinstance(concurrency_used, int)
        assert isinstance(sftp_concurrency_used, int)

    await redis_helper.execute(
        redis_stat,
        lambda r: r.set(
            f"keypair.concurrency_used.{access_key}",
            concurrency_used,
        ),
    )
    await redis_helper.execute(
        redis_stat,
        lambda r: r.set(
            f"keypair.sftp_concurrency_used.{access_key}",
            sftp_concurrency_used,
        ),
    )
