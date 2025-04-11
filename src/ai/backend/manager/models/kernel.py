from __future__ import annotations

import asyncio
import enum
import logging
import uuid
from collections.abc import Container, Mapping
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Optional,
    Sequence,
    TypedDict,
    cast,
)

import sqlalchemy as sa
from dateutil.tz import tzfile, tzutc
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, noload, relationship, selectinload

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelId,
    RedisConnectionInfo,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
    VFolderMount,
)
from ai.backend.logging import BraceStyleAdapter

from ..api.exceptions import (
    BackendError,
    KernelCreationFailed,
    KernelDestructionFailed,
    KernelExecutionFailed,
    KernelNotFound,
    KernelRestartFailed,
    SessionNotFound,
)
from ..defs import DEFAULT_ROLE
from ..exceptions import AgentError
from .base import (
    GUID,
    Base,
    EnumType,
    KernelIDColumn,
    ResourceSlotColumn,
    SessionIDColumnType,
    StrEnumType,
    StructuredJSONObjectListColumn,
    URLColumn,
)
from .user import users
from .utils import ExtendedAsyncSAEngine, JSONCoalesceExpr, execute_with_retry, sql_json_merge

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
    "AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES",
    "USER_RESOURCE_OCCUPYING_KERNEL_STATUSES",
    "RESOURCE_USAGE_KERNEL_STATUSES",
    "DEAD_KERNEL_STATUSES",
    "LIVE_STATUS",
    "recalc_concurrency_used",
)

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models.kernel"))


class KernelStatus(enum.StrEnum):
    # values are only meaningful inside the manager
    PENDING = "PENDING"
    # ---
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    # ---
    BUILDING = "BUILDING"
    PULLING = "PULLING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    # ---
    RUNNING = "RUNNING"
    RESTARTING = "RESTARTING"
    RESIZING = "RESIZING"
    SUSPENDED = "SUSPENDED"
    # ---
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


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
    "commit_session_to_file": KernelExecutionFailed,
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
        KernelStatus.SCHEDULED,
        KernelStatus.CANCELLED,
        KernelStatus.ERROR,
    },
    KernelStatus.SCHEDULED: {
        KernelStatus.PREPARING,
        KernelStatus.PULLING,
        KernelStatus.PREPARED,
        KernelStatus.CANCELLED,
        KernelStatus.ERROR,
    },
    KernelStatus.PREPARING: {
        KernelStatus.PULLING,
        KernelStatus.PREPARED,
        KernelStatus.CANCELLED,
        KernelStatus.ERROR,
    },
    KernelStatus.PULLING: {
        KernelStatus.PREPARED,
        KernelStatus.CANCELLED,
        KernelStatus.ERROR,
    },
    KernelStatus.PREPARED: {
        KernelStatus.CREATING,
        KernelStatus.CANCELLED,
        KernelStatus.ERROR,
    },
    KernelStatus.CREATING: {
        KernelStatus.RUNNING,
        KernelStatus.TERMINATING,
        KernelStatus.TERMINATED,
        KernelStatus.CANCELLED,
        KernelStatus.ERROR,
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
    KernelStatus.ERROR: {KernelStatus.TERMINATING, KernelStatus.TERMINATED},
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


class KernelRow(Base):
    __tablename__ = "kernels"

    # The Backend.AI-side UUID for each kernel
    # (mapped to a container in the docker backend and a pod in the k8s backend)
    id = KernelIDColumn()
    # session_id == id when the kernel is the main container in a multi-container session or a
    # single-container session.
    # Otherwise, it refers the kernel ID of the main container of the belonged multi-container session.
    session_id = sa.Column(
        "session_id",
        SessionIDColumnType,
        sa.ForeignKey("sessions.id"),
        unique=False,
        index=True,
        nullable=False,
    )
    session_creation_id = sa.Column(
        "session_creation_id", sa.String(length=32), unique=False, index=False
    )
    session_name = sa.Column(
        "session_name", sa.String(length=64), unique=False, index=True
    )  # previously sess_id
    session_type = sa.Column(
        "session_type",
        StrEnumType(SessionTypes, use_name=True),
        index=True,
        nullable=False,  # previously sess_type
        default=SessionTypes.INTERACTIVE,
        server_default=SessionTypes.INTERACTIVE.name,
    )
    cluster_mode = sa.Column(
        "cluster_mode",
        sa.String(length=16),
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE.name,
    )
    cluster_size = sa.Column("cluster_size", sa.Integer, nullable=False, default=1)
    cluster_role = sa.Column(
        "cluster_role", sa.String(length=16), nullable=False, default=DEFAULT_ROLE, index=True
    )
    cluster_idx = sa.Column("cluster_idx", sa.Integer, nullable=False, default=0)
    local_rank = sa.Column("local_rank", sa.Integer, nullable=False, default=0)
    cluster_hostname = sa.Column(
        "cluster_hostname", sa.String(length=64), nullable=False, default=default_hostname
    )
    uid = sa.Column("uid", sa.Integer, nullable=True, server_default=sa.null())
    main_gid = sa.Column("main_gid", sa.Integer, nullable=True, server_default=sa.null())
    gids = sa.Column("gids", sa.ARRAY(sa.Integer), nullable=True, server_default=sa.null())

    # Resource ownership
    scaling_group = sa.Column(
        "scaling_group", sa.ForeignKey("scaling_groups.name"), index=True, nullable=True
    )
    agent = sa.Column("agent", sa.String(length=64), sa.ForeignKey("agents.id"), nullable=True)
    agent_addr = sa.Column("agent_addr", sa.String(length=128), nullable=True)
    domain_name = sa.Column(
        "domain_name", sa.String(length=64), sa.ForeignKey("domains.name"), nullable=False
    )
    group_id = sa.Column("group_id", GUID, sa.ForeignKey("groups.id"), nullable=False)
    user_uuid = sa.Column("user_uuid", GUID, sa.ForeignKey("users.uuid"), nullable=False)
    access_key = sa.Column("access_key", sa.String(length=20), sa.ForeignKey("keypairs.access_key"))
    # `image` is a string representing canonical name which shaped "<REGISTRY>/<PROJECT>/<IMAGE_NAME>:<TAG>".
    image = sa.Column("image", sa.String(length=512))
    # ForeignKeyIDColumn("image_id", "images.id")
    architecture = sa.Column("architecture", sa.String(length=32), default="x86_64")
    registry = sa.Column("registry", sa.String(length=512))
    tag = sa.Column("tag", sa.String(length=64), nullable=True)
    # Resource occupation
    container_id = sa.Column("container_id", sa.String(length=64))
    occupied_slots = sa.Column("occupied_slots", ResourceSlotColumn(), nullable=False)
    requested_slots = sa.Column(
        "requested_slots", ResourceSlotColumn(), nullable=False, default=ResourceSlot()
    )
    occupied_shares = sa.Column(
        "occupied_shares", pgsql.JSONB(), nullable=False, default={}
    )  # legacy
    environ = sa.Column("environ", sa.ARRAY(sa.String), nullable=True)
    mounts = sa.Column(
        "mounts", sa.ARRAY(sa.String), nullable=True
    )  # list of list; legacy since 22.03
    mount_map = sa.Column(
        "mount_map", pgsql.JSONB(), nullable=True, default={}
    )  # legacy since 22.03
    vfolder_mounts = sa.Column(
        "vfolder_mounts", StructuredJSONObjectListColumn(VFolderMount), nullable=True
    )
    attached_devices = sa.Column("attached_devices", pgsql.JSONB(), nullable=True, default={})
    resource_opts = sa.Column("resource_opts", pgsql.JSONB(), nullable=True, default={})
    bootstrap_script = sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True)
    # Port mappings
    # If kernel_host is NULL, it is assumed to be same to the agent host or IP.
    kernel_host = sa.Column("kernel_host", sa.String(length=128), nullable=True)
    repl_in_port = sa.Column("repl_in_port", sa.Integer(), nullable=False)
    repl_out_port = sa.Column("repl_out_port", sa.Integer(), nullable=False)
    stdin_port = sa.Column("stdin_port", sa.Integer(), nullable=False)  # legacy for stream_pty
    stdout_port = sa.Column("stdout_port", sa.Integer(), nullable=False)  # legacy for stream_pty
    service_ports = sa.Column("service_ports", pgsql.JSONB(), nullable=True)
    preopen_ports = sa.Column("preopen_ports", sa.ARRAY(sa.Integer), nullable=True)
    use_host_network = sa.Column("use_host_network", sa.Boolean(), default=False, nullable=False)
    # Lifecycle
    created_at = sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
    )
    terminated_at = sa.Column(
        "terminated_at", sa.DateTime(timezone=True), nullable=True, default=sa.null(), index=True
    )
    starts_at = sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True, default=sa.null())
    status = sa.Column(
        "status",
        StrEnumType(KernelStatus),
        default=KernelStatus.PENDING,
        server_default=KernelStatus.PENDING.name,
        nullable=False,
        index=True,
    )
    status_changed = sa.Column(
        "status_changed", sa.DateTime(timezone=True), nullable=True, index=True
    )
    status_info = sa.Column("status_info", sa.Unicode(), nullable=True, default=sa.null())
    # status_info contains a kebab-cased string that expresses a summary of the last status change.
    # Examples: "user-requested", "self-terminated", "predicate-checks-failed", "no-available-instances"
    status_data = sa.Column("status_data", pgsql.JSONB(), nullable=True, default=sa.null())
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
    status_history = sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null())
    callback_url = sa.Column("callback_url", URLColumn, nullable=True, default=sa.null())
    startup_command = sa.Column("startup_command", sa.Text, nullable=True)
    result = sa.Column(
        "result",
        EnumType(SessionResult),
        default=SessionResult.UNDEFINED,
        server_default=SessionResult.UNDEFINED.name,
        nullable=False,
        index=True,
    )
    internal_data = sa.Column("internal_data", pgsql.JSONB(), nullable=True)
    container_log = sa.Column("container_log", sa.LargeBinary(), nullable=True)
    # Resource metrics measured upon termination
    num_queries = sa.Column("num_queries", sa.BigInteger(), default=0)
    last_stat = sa.Column("last_stat", pgsql.JSONB(), nullable=True, default=sa.null())

    __table_args__ = (
        # indexing
        sa.Index("ix_kernels_sess_id_role", "session_id", "cluster_role", unique=False),
        sa.Index("ix_kernels_status_role", "status", "cluster_role"),
        sa.Index(
            "ix_kernels_updated_order",
            sa.func.greatest("created_at", "terminated_at", "status_changed"),
            unique=False,
        ),
    )

    session = relationship("SessionRow", back_populates="kernels")
    image_row = relationship(
        "ImageRow",
        foreign_keys="KernelRow.image",
        primaryjoin="and_(KernelRow.image == ImageRow.name, KernelRow.architecture == ImageRow.architecture)",
    )
    agent_row = relationship("AgentRow", back_populates="kernels")
    group_row = relationship("GroupRow", back_populates="kernels")
    user_row = relationship("UserRow", back_populates="kernels")

    @property
    def image_ref(self) -> ImageRef | None:
        return self.image_row.image_ref if self.image_row else None

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

    @staticmethod
    async def batch_load_by_session_id(
        session: SASession, session_ids: list[uuid.UUID]
    ) -> list["KernelRow"]:
        query = sa.select(KernelRow).where(KernelRow.session_id.in_(session_ids))
        return (await session.execute(query)).scalars().all()

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
    async def get_kernel_to_update_status(
        cls,
        db_session: SASession,
        kernel_id: KernelId,
        *,
        for_update: bool = True,
    ) -> KernelRow:
        _stmt = sa.select(KernelRow).where(KernelRow.id == kernel_id)
        if for_update:
            _stmt = _stmt.with_for_update()
        kernel_row = cast(KernelRow | None, await db_session.scalar(_stmt))
        if kernel_row is None:
            raise KernelNotFound(f"Kernel not found (id:{kernel_id})")
        return kernel_row

    @classmethod
    async def get_bulk_kernels_to_update_status(
        cls,
        db_session: SASession,
        kernel_ids: Container[KernelId],
    ) -> list[KernelRow]:
        _stmt = sa.select(KernelRow).where(KernelRow.id.in_(kernel_ids))
        return (await db_session.scalars(_stmt)).all()

    def transit_status(
        self,
        status: KernelStatus,
        status_info: str | None = None,
        status_data: Mapping[str, Any] | JSONCoalesceExpr | None = None,
        status_changed_at: datetime | None = None,
    ) -> bool:
        """
        Check whether the transition from a current status to the given status is valid or not.
        Set the status if it is valid and return True.
        Else, return False.
        """
        if status not in KERNEL_STATUS_TRANSITION_MAP[self.status]:
            return False
        self.set_status(status, status_info, status_data, status_changed_at)
        return True

    def set_status(
        self,
        status: KernelStatus,
        status_info: str | None = None,
        status_data: Mapping[str, Any] | JSONCoalesceExpr | None = None,
        status_changed_at: datetime | None = None,
    ) -> None:
        """
        Set the status of the kernel.
        """
        now = status_changed_at or datetime.now(tzutc())
        if status in (KernelStatus.CANCELLED, KernelStatus.TERMINATED):
            self.terminated_at = now
        self.status_changed = now
        self.status = status
        self.status_history = {
            **self.status_history,
            status.name: now.isoformat(),
        }
        if status_info is not None:
            self.status_info = status_info
        if status_data is not None:
            self.status_data = status_data

    def delegate_ownership(self, user_uuid: uuid.UUID, access_key: AccessKey) -> None:
        self.user_uuid = user_uuid
        self.access_key = access_key

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
        assert status != KernelStatus.TERMINATED, (
            "TERMINATED status update must be handled in mark_kernel_terminated()"
        )
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
                    status.name: now.isoformat(),  # ["PULLING", "CREATING"]
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


# For compatibility
kernels = KernelRow.__table__

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
    async def batch_load_by_kernel_impl(
        cls,
        redis_stat: RedisConnectionInfo,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        """For cases where required to collect kernel metrics in bulk internally"""

        async def _build_pipeline(redis: Redis) -> Pipeline:
            pipe = redis.pipeline()
            for sess_id in session_ids:
                await pipe.get(str(sess_id))
            return pipe

        stats = []
        results = await redis_helper.execute(redis_stat, _build_pipeline)
        for result in results:
            if result is not None:
                stats.append(msgpack.unpackb(result))
            else:
                stats.append(None)
        return stats

    @classmethod
    async def batch_load_by_kernel(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        """wrapper of `KernelStatistics.batch_load_by_kernel_impl()` for aiodataloader"""
        return await cls.batch_load_by_kernel_impl(ctx.redis_stat, session_ids)

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


async def recalc_concurrency_used(
    db_sess: SASession,
    redis_stat: RedisConnectionInfo,
    access_key: AccessKey,
) -> None:
    concurrency_used: int
    from .session import PRIVATE_SESSION_TYPES

    async with db_sess.begin_nested():
        result = await db_sess.execute(
            sa.select(sa.func.count())
            .select_from(KernelRow)
            .where(
                (KernelRow.access_key == access_key)
                & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                & (KernelRow.session_type.not_in(PRIVATE_SESSION_TYPES))
            ),
        )
        concurrency_used = result.scalar()
        result = await db_sess.execute(
            sa.select(sa.func.count())
            .select_from(KernelRow)
            .where(
                (KernelRow.access_key == access_key)
                & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                & (KernelRow.session_type.in_(PRIVATE_SESSION_TYPES))
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
