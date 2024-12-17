from __future__ import annotations

import asyncio
import enum
import logging
import textwrap
from collections.abc import Iterable, Mapping, Sequence
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Final,
    List,
    Optional,
    TypeAlias,
    Union,
    cast,
    override,
)
from uuid import UUID

import aiotools
import graphene
import redis.exceptions
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, noload, relationship, selectinload

from ai.backend.common import redis_helper
from ai.backend.common.events import (
    EventDispatcher,
    EventProducer,
    SessionStartedEvent,
    SessionTerminatedEvent,
)
from ai.backend.common.plugin.hook import HookPluginContext
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
    AgentError,
    BackendError,
    KernelCreationFailed,
    KernelDestructionFailed,
    KernelExecutionFailed,
    KernelNotFound,
    KernelRestartFailed,
    MainKernelNotFound,
    SessionNotFound,
    TooManyKernelsFound,
    TooManySessionsMatched,
)
from ..defs import DEFAULT_ROLE
from .base import (
    GUID,
    Base,
    BigInt,
    EnumType,
    ForeignKeyIDColumn,
    Item,
    PaginatedList,
    ResourceSlotColumn,
    SessionIDColumn,
    StrEnumType,
    StructuredJSONObjectListColumn,
    URLColumn,
    batch_multiresult_in_session,
    batch_result_in_session,
)
from .group import GroupRow
from .image import ImageRow
from .kernel import ComputeContainer, KernelRow, KernelStatus
from .minilang import ArrayFieldItem, JSONFieldItem
from .minilang.ordering import ColumnMapType, QueryOrderParser
from .minilang.queryfilter import FieldSpecType, QueryFilterParser, enum_field_getter
from .network import NetworkRow, NetworkType
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    ScopeType,
    get_predefined_roles_in_scope,
)
from .rbac import (
    UserScope as UserRBACScope,
)
from .rbac.context import ClientContext
from .rbac.permission_defs import ComputeSessionPermission
from .user import UserRow
from .utils import (
    ExtendedAsyncSAEngine,
    JSONCoalesceExpr,
    agg_to_array,
    execute_with_retry,
    execute_with_txn_retry,
    sql_json_merge,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

    from ..registry import AgentRegistry
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = (
    "determine_session_status_by_kernels",
    "handle_session_exception",
    "SessionStatus",
    "ALLOWED_IMAGE_ROLES_FOR_SESSION_TYPE",
    "PRIVATE_SESSION_TYPES",
    "SESSION_STATUS_TRANSITION_MAP",
    "DEAD_SESSION_STATUSES",
    "AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES",
    "USER_RESOURCE_OCCUPYING_SESSION_STATUSES",
    "SessionRow",
    "SessionDependencyRow",
    "check_all_dependencies",
    "ComputeSession",
    "ComputeSessionList",
    "InferenceSession",
    "InferenceSessionList",
    "KernelLoadingStrategy",
)

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models.session"))


class SessionStatus(enum.StrEnum):
    # values are only meaningful inside the manager
    PENDING = "PENDING"
    # ---
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    # manager can set PENDING, SCHEDULED and PREPARING independently
    # ---
    PULLING = "PULLING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    # ---
    RUNNING = "RUNNING"
    RESTARTING = "RESTARTING"
    RUNNING_DEGRADED = "RUNNING_DEGRADED"
    # ---
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


FOLLOWING_SESSION_STATUSES = (
    # Session statuses that need to wait all kernels belonging to the session
    SessionStatus.PREPARED,
    SessionStatus.RUNNING,
    SessionStatus.TERMINATED,
)
LEADING_SESSION_STATUSES = tuple(
    # Session statuses that declare first, do not need to wait any sibling kernel
    s
    for s in SessionStatus
    if s not in FOLLOWING_SESSION_STATUSES
)

DEAD_SESSION_STATUSES = (
    SessionStatus.CANCELLED,
    SessionStatus.TERMINATED,
)

# statuses to consider when calculating current resource usage
AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES = tuple(
    e
    for e in SessionStatus
    if e
    not in (
        SessionStatus.TERMINATED,
        SessionStatus.PENDING,
        SessionStatus.CANCELLED,
    )
)

USER_RESOURCE_OCCUPYING_SESSION_STATUSES = tuple(
    e
    for e in SessionStatus
    if e
    not in (
        SessionStatus.TERMINATING,
        SessionStatus.TERMINATED,
        SessionStatus.PENDING,
        SessionStatus.CANCELLED,
    )
)

PRIVATE_SESSION_TYPES = (SessionTypes.SYSTEM,)
SESSION_PRIORITY_DEFUALT: Final = 10
SESSION_PRIORITY_MIN: Final = 0
SESSION_PRIORITY_MAX: Final = 100

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
    "trigger_batch_execution": KernelExecutionFailed,
}


KERNEL_SESSION_STATUS_MAPPING: Mapping[KernelStatus, SessionStatus] = {
    KernelStatus.PENDING: SessionStatus.PENDING,
    KernelStatus.SCHEDULED: SessionStatus.SCHEDULED,
    KernelStatus.PREPARING: SessionStatus.PREPARING,
    KernelStatus.BUILDING: SessionStatus.PREPARING,
    KernelStatus.PULLING: SessionStatus.PULLING,
    KernelStatus.PREPARED: SessionStatus.PREPARED,
    KernelStatus.CREATING: SessionStatus.CREATING,
    KernelStatus.RUNNING: SessionStatus.RUNNING,
    KernelStatus.RESTARTING: SessionStatus.RESTARTING,
    KernelStatus.RESIZING: SessionStatus.RUNNING,
    KernelStatus.SUSPENDED: SessionStatus.ERROR,
    KernelStatus.TERMINATING: SessionStatus.TERMINATING,
    KernelStatus.TERMINATED: SessionStatus.TERMINATED,
    KernelStatus.ERROR: SessionStatus.ERROR,
    KernelStatus.CANCELLED: SessionStatus.CANCELLED,
}

SESSION_KERNEL_STATUS_MAPPING: Mapping[SessionStatus, KernelStatus] = {
    SessionStatus.PENDING: KernelStatus.PENDING,
    SessionStatus.SCHEDULED: KernelStatus.SCHEDULED,
    SessionStatus.PREPARING: KernelStatus.PREPARING,
    SessionStatus.PULLING: KernelStatus.PULLING,
    SessionStatus.PREPARED: KernelStatus.PREPARED,
    SessionStatus.CREATING: KernelStatus.CREATING,
    SessionStatus.RUNNING: KernelStatus.RUNNING,
    SessionStatus.RESTARTING: KernelStatus.RESTARTING,
    SessionStatus.TERMINATING: KernelStatus.TERMINATING,
    SessionStatus.TERMINATED: KernelStatus.TERMINATED,
    SessionStatus.ERROR: KernelStatus.ERROR,
    SessionStatus.CANCELLED: KernelStatus.CANCELLED,
}

SESSION_STATUS_TRANSITION_MAP: Mapping[SessionStatus, set[SessionStatus]] = {
    SessionStatus.PENDING: {
        SessionStatus.SCHEDULED,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.SCHEDULED: {
        SessionStatus.PREPARING,
        SessionStatus.PULLING,
        SessionStatus.PREPARED,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.PREPARING: {
        SessionStatus.PULLING,
        SessionStatus.PREPARED,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.PULLING: {
        SessionStatus.PREPARED,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.PREPARED: {
        SessionStatus.PREPARING,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.CREATING: {
        SessionStatus.RUNNING,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.RUNNING: {
        SessionStatus.RESTARTING,
        SessionStatus.RUNNING_DEGRADED,
        SessionStatus.TERMINATING,
        SessionStatus.TERMINATED,
        SessionStatus.ERROR,
    },
    SessionStatus.RESTARTING: {
        SessionStatus.RUNNING,
        SessionStatus.RUNNING_DEGRADED,
        SessionStatus.TERMINATING,
        SessionStatus.TERMINATED,
        SessionStatus.ERROR,
    },
    SessionStatus.RUNNING_DEGRADED: {
        SessionStatus.RUNNING,
        SessionStatus.TERMINATING,
        SessionStatus.TERMINATED,
        SessionStatus.ERROR,
    },
    SessionStatus.TERMINATING: {SessionStatus.TERMINATED, SessionStatus.ERROR},
    SessionStatus.TERMINATED: set(),
    SessionStatus.ERROR: {SessionStatus.TERMINATING, SessionStatus.TERMINATED},
    SessionStatus.CANCELLED: set(),
}


def determine_session_status_by_kernels(kernels: Sequence[KernelRow]) -> SessionStatus:
    if not kernels:
        raise KernelNotFound
    candidate = KERNEL_SESSION_STATUS_MAPPING[kernels[0].status]
    if len(kernels) == 1:
        return candidate

    for k in kernels:
        match k.status:
            case KernelStatus.ERROR:
                # If any kernel status is ERROR, determines session status as ERROR
                return SessionStatus.ERROR
            case (
                KernelStatus.BUILDING
                | KernelStatus.RESTARTING
                | KernelStatus.RESIZING
                | KernelStatus.SUSPENDED
            ):
                raise RuntimeError("Status not used.")

        match candidate:
            case SessionStatus.PENDING:
                match k.status:
                    case KernelStatus.PENDING:
                        continue
                    case KernelStatus.CANCELLED:
                        candidate = SessionStatus.CANCELLED
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.SCHEDULED:
                match k.status:
                    case KernelStatus.SCHEDULED | KernelStatus.PREPARED:
                        continue
                    case KernelStatus.CANCELLED:
                        candidate = SessionStatus.CANCELLED
                    case KernelStatus.PULLING:
                        candidate = SessionStatus.PULLING
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.PREPARING:
                match k.status:
                    case KernelStatus.PREPARING | KernelStatus.PREPARED:
                        continue
                    case KernelStatus.PULLING:
                        candidate = SessionStatus.PULLING
                    case KernelStatus.CANCELLED:
                        candidate = SessionStatus.CANCELLED
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.PULLING:
                match k.status:
                    case KernelStatus.PULLING | KernelStatus.PREPARING | KernelStatus.PREPARED:
                        continue
                    case KernelStatus.CANCELLED:
                        candidate = SessionStatus.CANCELLED
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.PREPARED:
                match k.status:
                    case KernelStatus.PREPARED:
                        continue
                    case KernelStatus.PREPARING:
                        candidate = SessionStatus.PREPARING
                    case KernelStatus.PULLING:
                        candidate = SessionStatus.PULLING
                    case KernelStatus.CANCELLED:
                        candidate = SessionStatus.CANCELLED
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.CREATING:
                match k.status:
                    case KernelStatus.CREATING | KernelStatus.RUNNING:
                        continue
                    case KernelStatus.CANCELLED:
                        candidate = SessionStatus.CANCELLED
                    case _:
                        # Set status to ERROR if any kernel is in exceptional state
                        return SessionStatus.ERROR
            case SessionStatus.CANCELLED:
                match k.status:
                    case (
                        KernelStatus.CANCELLED
                        | KernelStatus.PENDING
                        | KernelStatus.SCHEDULED
                        | KernelStatus.PREPARING
                        | KernelStatus.PULLING
                        | KernelStatus.PREPARED
                    ):
                        continue
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.RUNNING:
                match k.status:
                    case KernelStatus.RUNNING:
                        continue
                    case KernelStatus.CREATING:
                        candidate = SessionStatus.CREATING
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.TERMINATING:
                match k.status:
                    case KernelStatus.TERMINATING | KernelStatus.TERMINATED:
                        continue
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.TERMINATED:
                match k.status:
                    case KernelStatus.TERMINATED:
                        continue
                    case KernelStatus.TERMINATING:
                        candidate = SessionStatus.TERMINATING
                    case _:
                        return SessionStatus.ERROR
            case SessionStatus.RESTARTING | SessionStatus.RUNNING_DEGRADED:
                raise RuntimeError("Status not used.")
    return candidate


@actxmgr
async def handle_session_exception(
    db: ExtendedAsyncSAEngine,
    op: str,
    session_id: SessionId,
    error_callback=None,
    cancellation_callback=None,
    set_error: bool = False,
) -> AsyncIterator[None]:
    exc_class = OP_EXC[op]
    try:
        yield
    except asyncio.TimeoutError:
        if set_error:
            await SessionRow.set_session_status(
                db,
                session_id,
                SessionStatus.ERROR,
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
            await SessionRow.set_session_status(
                db,
                session_id,
                SessionStatus.ERROR,
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
            await SessionRow.set_session_status(
                db,
                session_id,
                SessionStatus.ERROR,
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


def _build_session_fetch_query(
    base_cond,
    access_key: AccessKey | None = None,
    *,
    allow_stale: bool = True,
    for_update: bool = False,
    do_ordering: bool = False,
    max_matches: Optional[int] = None,
    eager_loading_op: Optional[Sequence] = None,
):
    cond = base_cond
    if access_key:
        cond = cond & (SessionRow.access_key == access_key)
    if not allow_stale:
        cond = cond & (~SessionRow.status.in_(DEAD_SESSION_STATUSES))
    query = (
        sa.select(SessionRow)
        .where(cond)
        .order_by(sa.desc(SessionRow.created_at))
        .execution_options(populate_existing=True)
    )
    if max_matches is not None:
        query = query.limit(max_matches).offset(0)
    if for_update:
        query = query.with_for_update()
    if do_ordering:
        query = query.order_by(SessionRow.created_at)
    if eager_loading_op is not None:
        query = query.options(*eager_loading_op)

    return query


async def _match_sessions_by_id(
    db_session: SASession,
    session_id_or_list: SessionId | list[SessionId],
    access_key: AccessKey | None = None,
    *,
    allow_prefix: bool = False,
    allow_stale: bool = True,
    for_update: bool = False,
    max_matches: Optional[int] = None,
    eager_loading_op: Optional[Sequence] = None,
) -> List[SessionRow]:
    if isinstance(session_id_or_list, list):
        cond = SessionRow.id.in_(session_id_or_list)
    else:
        if allow_prefix:
            cond = sa.sql.expression.cast(SessionRow.id, sa.String).like(f"{session_id_or_list}%")
        else:
            cond = SessionRow.id == session_id_or_list
    query = _build_session_fetch_query(
        cond,
        access_key,
        max_matches=max_matches,
        allow_stale=allow_stale,
        for_update=for_update,
        eager_loading_op=eager_loading_op,
    )

    result = await db_session.execute(query)
    return result.scalars().all()


async def _match_sessions_by_name(
    db_session: SASession,
    session_name: str,
    access_key: AccessKey,
    *,
    allow_prefix: bool = False,
    allow_stale: bool = True,
    for_update: bool = False,
    max_matches: Optional[int] = None,
    eager_loading_op: Optional[Sequence] = None,
) -> List[SessionRow]:
    if allow_prefix:
        cond = sa.sql.expression.cast(SessionRow.name, sa.String).like(f"{session_name}%")
    else:
        cond = SessionRow.name == session_name
    query = _build_session_fetch_query(
        cond,
        access_key,
        max_matches=max_matches,
        allow_stale=allow_stale,
        for_update=for_update,
        eager_loading_op=eager_loading_op,
    )
    result = await db_session.execute(query)
    return result.scalars().all()


COMPUTE_CONCURRENCY_USED_KEY_PREFIX = "keypair.concurrency_used."
SYSTEM_CONCURRENCY_USED_KEY_PREFIX = "keypair.sftp_concurrency_used."


@dataclass
class ConcurrencyUsed:
    access_key: AccessKey
    compute_session_ids: set[SessionId] = field(default_factory=set)
    system_session_ids: set[SessionId] = field(default_factory=set)

    @property
    def compute_concurrency_used_key(self) -> str:
        return f"{COMPUTE_CONCURRENCY_USED_KEY_PREFIX}{self.access_key}"

    @property
    def system_concurrency_used_key(self) -> str:
        return f"{SYSTEM_CONCURRENCY_USED_KEY_PREFIX}{self.access_key}"

    def to_cnt_map(self) -> Mapping[str, int]:
        return {
            self.compute_concurrency_used_key: len(self.compute_session_ids),
            self.system_concurrency_used_key: len(self.system_session_ids),
        }


class SessionOp(enum.StrEnum):
    CREATE = "create_session"
    DESTROY = "destroy_session"
    RESTART = "restart_session"
    EXECUTE = "execute"
    REFRESH = "refresh_session"
    SHUTDOWN_SERVICE = "shutdown_service"
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    LIST_FILE = "list_files"
    GET_AGENT_LOGS = "get_logs_from_agent"


class KernelLoadingStrategy(enum.StrEnum):
    ALL_KERNELS = "all"
    MAIN_KERNEL_ONLY = "main"
    NONE = "none"


ALLOWED_IMAGE_ROLES_FOR_SESSION_TYPE: Mapping[SessionTypes, tuple[str, ...]] = {
    SessionTypes.BATCH: ("COMPUTE",),
    SessionTypes.INTERACTIVE: ("COMPUTE",),
    SessionTypes.INFERENCE: ("INFERENCE",),
    SessionTypes.SYSTEM: ("SYSTEM",),
}


class SessionRow(Base):
    __tablename__ = "sessions"
    id = SessionIDColumn()
    creation_id = sa.Column("creation_id", sa.String(length=32), unique=False, index=False)
    name = sa.Column("name", sa.String(length=64), unique=False, index=True)
    session_type = sa.Column(
        "session_type",
        StrEnumType(SessionTypes, use_name=True),
        index=True,
        nullable=False,  # previously sess_type
        default=SessionTypes.INTERACTIVE,
        server_default=SessionTypes.INTERACTIVE.name,
    )
    priority = sa.Column(
        "priority",
        sa.Integer(),
        nullable=False,
        default=SESSION_PRIORITY_DEFUALT,
        index=True,
    )

    cluster_mode = sa.Column(
        "cluster_mode",
        sa.String(length=16),
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE.name,
    )
    cluster_size = sa.Column("cluster_size", sa.Integer, nullable=False, default=1)
    agent_ids = sa.Column("agent_ids", sa.ARRAY(sa.String), nullable=True)
    kernels = relationship("KernelRow", back_populates="session")

    # Resource ownership
    scaling_group_name = sa.Column(
        "scaling_group_name", sa.ForeignKey("scaling_groups.name"), index=True, nullable=True
    )
    scaling_group = relationship("ScalingGroupRow", back_populates="sessions")
    target_sgroup_names = sa.Column(
        "target_sgroup_names",
        sa.ARRAY(sa.String(length=64)),
        default="{}",
        server_default="{}",
        nullable=True,
    )
    domain_name = sa.Column(
        "domain_name", sa.String(length=64), sa.ForeignKey("domains.name"), nullable=False
    )
    domain = relationship("DomainRow", back_populates="sessions")
    group_id = ForeignKeyIDColumn("group_id", "groups.id", nullable=False)
    group = relationship("GroupRow", back_populates="sessions")
    user_uuid = ForeignKeyIDColumn("user_uuid", "users.uuid", nullable=False)
    user = relationship("UserRow", back_populates="sessions")
    access_key = sa.Column("access_key", sa.String(length=20), sa.ForeignKey("keypairs.access_key"))
    access_key_row = relationship("KeyPairRow", back_populates="sessions")

    # `image` column is identical to kernels `image` column.
    images = sa.Column("images", sa.ARRAY(sa.String), nullable=True)
    tag = sa.Column("tag", sa.String(length=64), nullable=True)

    # Resource occupation
    # occupied_slots = sa.Column('occupied_slots', ResourceSlotColumn(), nullable=False)
    occupying_slots = sa.Column("occupying_slots", ResourceSlotColumn(), nullable=False)
    requested_slots = sa.Column("requested_slots", ResourceSlotColumn(), nullable=False)
    vfolder_mounts = sa.Column(
        "vfolder_mounts", StructuredJSONObjectListColumn(VFolderMount), nullable=True
    )
    environ = sa.Column("environ", pgsql.JSONB(), nullable=True, default={})
    bootstrap_script = sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True)
    use_host_network = sa.Column("use_host_network", sa.Boolean(), default=False, nullable=False)

    # Lifecycle
    timeout = sa.Column("timeout", sa.BigInteger(), nullable=True)
    batch_timeout = sa.Column(
        "batch_timeout", sa.BigInteger(), nullable=True
    )  # Used to set timeout of batch sessions
    created_at = sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
    )
    terminated_at = sa.Column(
        "terminated_at", sa.DateTime(timezone=True), nullable=True, default=sa.null(), index=True
    )
    starts_at = sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True, default=sa.null())
    status = sa.Column(
        "status",
        StrEnumType(SessionStatus),
        default=SessionStatus.PENDING,
        server_default=SessionStatus.PENDING.name,
        nullable=False,
        index=True,
    )
    status_info = sa.Column("status_info", sa.Unicode(), nullable=True, default=sa.null())

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

    # Resource metrics measured upon termination
    num_queries = sa.Column("num_queries", sa.BigInteger(), default=0)
    last_stat = sa.Column("last_stat", pgsql.JSONB(), nullable=True, default=sa.null())

    network_type = sa.Column("network_type", StrEnumType(NetworkType), nullable=True)
    """Setting this column to null means this session does not utilize inter-container networking feature"""
    network_id = sa.Column("network_id", sa.String(length=128), nullable=True)
    """
    Depending on the network_type, this column may contain a network ID or other information.
    Use `get_network_ref()` method to reveal actual network ref (generated by network plugin).
    """

    routing = relationship("RoutingRow", back_populates="session_row")

    __table_args__ = (
        # indexing
        sa.Index(
            "ix_sessions_updated_order",
            sa.func.greatest(
                "created_at",
                "terminated_at",
            ),
            unique=False,
        ),
        sa.Index("ix_sessions_vfolder_mounts", "vfolder_mounts", postgresql_using="gin"),
        sa.Index("ix_session_status_with_priority", "status", "priority"),
    )

    @property
    def main_kernel(self) -> KernelRow:
        kerns = tuple(kern for kern in self.kernels if kern.cluster_role == DEFAULT_ROLE)
        if len(kerns) > 1:
            raise TooManyKernelsFound(
                f"Session (id: {self.id}) has more than 1 main kernel.",
            )
        if len(kerns) == 0:
            raise MainKernelNotFound(
                f"Session (id: {self.id}) has no main kernel.",
            )
        return kerns[0]

    @property
    def status_changed(self) -> Optional[datetime]:
        if self.status_history is None:
            return None
        try:
            return datetime.fromisoformat(self.status_history[self.status.name])
        except KeyError:
            return None

    @property
    def resource_opts(self) -> dict[str, Any]:
        return {kern.cluster_hostname: kern.resource_opts for kern in self.kernels}

    @property
    def is_private(self) -> bool:
        return self.session_type in PRIVATE_SESSION_TYPES

    def get_kernel_by_id(self, kernel_id: KernelId) -> KernelRow:
        kerns = tuple(kern for kern in self.kernels if kern.id == kernel_id)
        if len(kerns) > 1:
            raise TooManyKernelsFound(f"Multiple kernels found (id:{kernel_id}).")
        if len(kerns) == 0:
            raise KernelNotFound(f"Session has no such kernel (sid:{self.id}, kid:{kernel_id}))")
        return kerns[0]

    def get_kernel_by_cluster_name(self, cluster_name: str) -> KernelRow:
        kerns = tuple(kern for kern in self.kernels if kern.cluster_name == cluster_name)
        if len(kerns) > 1:
            raise TooManyKernelsFound(
                f"Session (id: {self.id}) has more than 1 kernel with {cluster_name = }",
            )
        if len(kerns) == 0:
            raise MainKernelNotFound(
                f"Session (id: {self.id}) has no kernel with {cluster_name = }.",
            )
        return kerns[0]

    @classmethod
    async def get_session_id_by_kernel(
        cls, db: ExtendedAsyncSAEngine, kernel_id: KernelId
    ) -> SessionId:
        query = sa.select(KernelRow.session_id).where(KernelRow.id == kernel_id)
        async with db.begin_readonly_session() as db_session:
            return await db_session.scalar(query)

    @classmethod
    async def get_sessions_by_status(
        cls,
        db_session: SASession,
        status: SessionStatus,
        *,
        load_kernel_image: bool = False,
    ) -> list[SessionRow]:
        load_options = selectinload(SessionRow.kernels)
        if load_kernel_image:
            load_options = load_options.options(
                joinedload(KernelRow.image_row).options(joinedload(ImageRow.registry_row))
            )
        stmt = sa.select(SessionRow).where(SessionRow.status == status).options(load_options)
        return (await db_session.scalars(stmt)).all()

    @classmethod
    async def get_session_to_determine_status(
        cls, db_session: SASession, session_id: SessionId
    ) -> SessionRow:
        stmt = (
            sa.select(SessionRow)
            .where(SessionRow.id == session_id)
            .options(
                selectinload(SessionRow.kernels).options(
                    load_only(
                        KernelRow.agent,
                        KernelRow.agent_addr,
                        KernelRow.startup_command,
                        KernelRow.status,
                        KernelRow.cluster_role,
                        KernelRow.status_info,
                        KernelRow.occupied_slots,
                    )
                ),
            )
        )
        session_row = cast(SessionRow | None, await db_session.scalar(stmt))
        if session_row is None:
            raise SessionNotFound(f"Session not found (id:{session_id})")
        return session_row

    def determine_and_set_status(
        self,
        status_info: str | None = None,
        status_data: Mapping[str, Any] | JSONCoalesceExpr | None = None,
        status_changed_at: datetime | None = None,
    ) -> bool:
        """
        Determine the current status of a session based on its sibling kernels.
        If it is possible to transit from the current status to the determined status, set status.
        Else, do nothing.
        Return True if a transition happened, else return False.
        """

        determined_status = determine_session_status_by_kernels(self.kernels)
        if determined_status not in SESSION_STATUS_TRANSITION_MAP[self.status]:
            return False

        self.set_status(determined_status, status_info, status_data, status_changed_at)
        return True

    def set_status(
        self,
        status: SessionStatus,
        status_info: str | None = None,
        status_data: Mapping[str, Any] | JSONCoalesceExpr | None = None,
        status_changed_at: datetime | None = None,
    ) -> None:
        """
        Set the status of the session.
        """
        now = status_changed_at or datetime.now(tzutc())
        if status in (SessionStatus.CANCELLED, SessionStatus.TERMINATED):
            self.terminated_at = now
        self.status = status
        self.status_history = {
            **self.status_history,
            status.name: now.isoformat(),
        }
        if status_data is not None:
            self.status_data = status_data

        _status_info: str | None = None
        if status_info is None:
            _status_info = self.main_kernel.status_info
        else:
            _status_info = status_info
        if _status_info is not None:
            self.status_info = _status_info

    @staticmethod
    async def set_session_status(
        db: ExtendedAsyncSAEngine,
        session_id: SessionId,
        status: SessionStatus,
        *,
        status_data: Optional[Mapping[str, Any]] = None,
        reason: Optional[str] = None,
        status_changed_at: Optional[datetime] = None,
    ) -> None:
        if status_changed_at is None:
            now = datetime.now(tzutc())
        else:
            now = status_changed_at
        data = {
            "status": status,
            "status_history": sql_json_merge(
                SessionRow.status_history,
                (),
                {
                    status.name: datetime.now(tzutc()).isoformat(),
                },
            ),
        }
        if status_data is not None:
            data["status_data"] = status_data
        if reason is not None:
            data["status_info"] = reason
        if status in (SessionStatus.CANCELLED, SessionStatus.TERMINATED):
            data["terminated_at"] = now

        async def _update() -> None:
            async with db.begin_session() as db_sess:
                query = sa.update(SessionRow).values(**data).where(SessionRow.id == session_id)
                await db_sess.execute(query)

        await execute_with_retry(_update)

    @classmethod
    async def set_session_result(
        cls,
        db: ExtendedAsyncSAEngine,
        session_id: SessionId,
        success: bool,
        exit_code: int,
    ) -> None:
        # TODO: store exit code?
        data = {
            "result": SessionResult.SUCCESS if success else SessionResult.FAILURE,
        }

        async def _update() -> None:
            async with db.begin_session() as db_sess:
                query = sa.update(SessionRow).values(**data).where(SessionRow.id == session_id)
                await db_sess.execute(query)

        await execute_with_retry(_update)

    @classmethod
    async def match_sessions(
        cls,
        db_session: SASession,
        session_reference: str | UUID | list[UUID],
        access_key: Optional[AccessKey],
        *,
        allow_prefix: bool = False,
        allow_stale: bool = True,
        for_update: bool = False,
        max_matches: Optional[int] = 10,
        eager_loading_op: Optional[Sequence] = None,
    ) -> List[SessionRow]:
        """
        Match the prefix of session ID or session name among the sessions
        that belongs to the given access key, and return the list of SessionRow.
        """

        if isinstance(session_reference, list):
            query_list = [
                aiotools.apartial(
                    _match_sessions_by_id,
                    session_id_or_list=session_reference,
                    allow_prefix=False,
                )
            ]
        else:
            query_list = [
                aiotools.apartial(
                    _match_sessions_by_name,
                    session_name=str(session_reference),
                    allow_prefix=allow_prefix,
                )
            ]
            try:
                session_id = UUID(str(session_reference))
                # Fetch id-based query first
                query_list = [
                    aiotools.apartial(
                        _match_sessions_by_id,
                        session_id_or_list=SessionId(session_id),
                        allow_prefix=False,
                    ),
                    *query_list,
                ]
                if allow_prefix:
                    query_list = [
                        aiotools.apartial(
                            _match_sessions_by_id,
                            session_id_or_list=SessionId(session_id),
                            allow_prefix=True,
                        ),
                        *query_list,
                    ]
            except ValueError:
                pass

        for fetch_func in query_list:
            rows = await fetch_func(
                db_session,
                access_key=access_key,
                allow_stale=allow_stale,
                for_update=for_update,
                max_matches=max_matches,
                eager_loading_op=eager_loading_op,
            )
            if not rows:
                continue
            return rows
        return []

    @classmethod
    async def get_session(
        cls,
        db_session: SASession,
        session_name_or_id: Union[str, UUID],
        access_key: Optional[AccessKey] = None,
        *,
        allow_stale: bool = False,
        for_update: bool = False,
        kernel_loading_strategy: KernelLoadingStrategy = KernelLoadingStrategy.NONE,
        eager_loading_op: list[Any] | None = None,
    ) -> SessionRow:
        """
        Retrieve the session information by session's UUID,
        or session's name paired with access_key.
        This will return the information of the session and the sibling kernel(s).

        :param db_session: Database connection to use when fetching row.
        :param session_name_or_id: Name or ID (UUID) of session to look up.
        :param access_key: Access key used to create session.
        :param allow_stale: If set to True, filter "inactive" sessions as well as "active" ones.
                            Otherwise filter "active" sessions only.
        :param for_update: Apply for_update during executing select query.
        :param kernel_loading_strategy: Determines JOIN strategy of `kernels` relation when fetching session rows.
        :param eager_loading_op: Extra loading operators to be passed directly to `match_sessions()` API.
        """
        _eager_loading_op = eager_loading_op or []
        match kernel_loading_strategy:
            case KernelLoadingStrategy.ALL_KERNELS:
                _eager_loading_op.extend([
                    noload("*"),
                    selectinload(SessionRow.kernels).options(
                        noload("*"),
                        selectinload(KernelRow.agent_row).noload("*"),
                    ),
                ])
            case KernelLoadingStrategy.MAIN_KERNEL_ONLY:
                kernel_rel = SessionRow.kernels
                kernel_rel.and_(KernelRow.cluster_role == DEFAULT_ROLE)
                _eager_loading_op.extend([
                    noload("*"),
                    selectinload(kernel_rel).options(
                        noload("*"),
                        selectinload(KernelRow.agent_row).noload("*"),
                    ),
                ])

        session_list = await cls.match_sessions(
            db_session,
            session_name_or_id,
            access_key,
            allow_stale=allow_stale,
            for_update=for_update,
            eager_loading_op=_eager_loading_op,
        )
        if not session_list:
            raise SessionNotFound(f"Session (id={session_name_or_id}) does not exist.")
        if len(session_list) > 1:
            session_infos = [
                {
                    "session_id": sess.id,
                    "session_name": sess.name,
                    "status": sess.status,
                    "created_at": sess.created_at,
                }
                for sess in session_list
            ]
            raise TooManySessionsMatched(extra_data={"matches": session_infos})
        return session_list[0]

    @classmethod
    async def list_sessions(
        cls,
        db_session: SASession,
        session_ids: list[UUID],
        access_key: Optional[AccessKey] = None,
        *,
        allow_stale: bool = False,
        for_update: bool = False,
        kernel_loading_strategy=KernelLoadingStrategy.NONE,
        eager_loading_op: list[Any] | None = None,
        max_load_count: Optional[int] = None,
    ) -> Iterable[SessionRow]:
        _eager_loading_op = eager_loading_op or []
        match kernel_loading_strategy:
            case KernelLoadingStrategy.ALL_KERNELS:
                _eager_loading_op.extend([
                    noload("*"),
                    selectinload(SessionRow.kernels).options(
                        noload("*"),
                        selectinload(KernelRow.agent_row).noload("*"),
                    ),
                ])
            case KernelLoadingStrategy.MAIN_KERNEL_ONLY:
                kernel_rel = SessionRow.kernels
                kernel_rel.and_(KernelRow.cluster_role == DEFAULT_ROLE)
                _eager_loading_op.extend([
                    noload("*"),
                    selectinload(kernel_rel).options(
                        noload("*"),
                        selectinload(KernelRow.agent_row).noload("*"),
                    ),
                ])

        session_list = await cls.match_sessions(
            db_session,
            session_ids,
            access_key,
            allow_stale=allow_stale,
            for_update=for_update,
            eager_loading_op=_eager_loading_op,
            max_matches=max_load_count,
        )
        try:
            return session_list
        except IndexError:
            raise SessionNotFound(f"Session (ids={session_ids}) does not exist.")

    @classmethod
    async def get_session_by_id(
        cls,
        db_session: SASession,
        session_id: SessionId,
        access_key: Optional[AccessKey] = None,
        *,
        max_matches: int | None = None,
        allow_stale: bool = True,
        for_update: bool = False,
        eager_loading_op=None,
    ) -> SessionRow:
        sessions = await _match_sessions_by_id(
            db_session,
            session_id,
            access_key,
            max_matches=max_matches,
            allow_stale=allow_stale,
            for_update=for_update,
            eager_loading_op=eager_loading_op,
            allow_prefix=False,
        )
        try:
            return sessions[0]
        except IndexError:
            raise SessionNotFound(f"Session (id={session_id}) does not exist.")

    @classmethod
    async def get_sgroup_managed_sessions(
        cls,
        db_sess: SASession,
        sgroup_name: str,
    ) -> List[SessionRow]:
        candidate_statues = (SessionStatus.PENDING, *AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES)
        query = (
            sa.select(SessionRow)
            .where(
                (SessionRow.scaling_group_name == sgroup_name)
                & (SessionRow.status.in_(candidate_statues))
            )
            .options(
                noload("*"),
                selectinload(SessionRow.group).options(noload("*")),
                selectinload(SessionRow.domain).options(noload("*")),
                selectinload(SessionRow.access_key_row).options(noload("*")),
                selectinload(SessionRow.kernels).options(noload("*")),
            )
        )
        result = await db_sess.execute(query)
        return result.scalars().all()

    async def get_network_ref(self, db_sess: SASession) -> str | None:
        if not self.network_id or not self.network_type:
            return None
        match self.network_type:
            case NetworkType.VOLATILE | NetworkType.HOST:
                return self.network_id
            case NetworkType.PERSISTENT:
                network_row = await NetworkRow.get(db_sess, UUID(self.network_id))
                return network_row.ref_name
            case _:
                return None


class SessionLifecycleManager:
    status_set_key = "session_status_update"

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        redis_obj: RedisConnectionInfo,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        hook_plugin_ctx: HookPluginContext,
        registry: AgentRegistry,
    ) -> None:
        self.db = db
        self.redis_obj = redis_obj
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.hook_plugin_ctx = hook_plugin_ctx
        self.registry = registry

        def _encode(sid: SessionId) -> bytes:
            return sid.bytes

        def _decode(raw_sid: bytes) -> SessionId:
            return SessionId(UUID(bytes=raw_sid))

        self._encoder = _encode
        self._decoder = _decode

    async def _transit_session_status(
        self,
        db_conn: SAConnection,
        session_id: SessionId,
        status_changed_at: datetime | None = None,
    ) -> tuple[SessionRow, bool]:
        now = status_changed_at or datetime.now(tzutc())

        async def _get_and_transit(
            db_session: SASession,
        ) -> tuple[SessionRow, bool]:
            session_row = await SessionRow.get_session_to_determine_status(db_session, session_id)
            transited = session_row.determine_and_set_status(status_changed_at=now)

            def _calculate_session_occupied_slots(session_row: SessionRow):
                session_occupying_slots = ResourceSlot()
                for row in session_row.kernels:
                    kernel_row = cast(KernelRow, row)
                    kernel_allocs = kernel_row.occupied_slots
                    session_occupying_slots.sync_keys(kernel_allocs)
                    for key, val in session_occupying_slots.items():
                        session_occupying_slots[key] = str(
                            Decimal(val) + Decimal(kernel_allocs[key])
                        )
                session_row.occupying_slots = session_occupying_slots

            match session_row.status:
                case SessionStatus.CREATING:
                    _calculate_session_occupied_slots(session_row)
                case SessionStatus.RUNNING if transited:
                    _calculate_session_occupied_slots(session_row)

            return session_row, transited

        return await execute_with_txn_retry(_get_and_transit, self.db.begin_session, db_conn)

    async def _post_status_transition(
        self,
        session_row: SessionRow,
    ) -> None:
        match session_row.status:
            case SessionStatus.RUNNING:
                log.debug(
                    "Producing SessionStartedEvent({}, {})",
                    session_row.id,
                    session_row.creation_id,
                )
                await self.event_producer.produce_event(
                    SessionStartedEvent(session_row.id, session_row.creation_id),
                )
                await self.hook_plugin_ctx.notify(
                    "POST_START_SESSION",
                    (
                        session_row.id,
                        session_row.name,
                        session_row.access_key,
                    ),
                )
                if session_row.session_type == SessionTypes.BATCH:
                    await self.registry.trigger_batch_execution(session_row)
            case SessionStatus.TERMINATED:
                await self.event_producer.produce_event(
                    SessionTerminatedEvent(session_row.id, session_row.main_kernel.status_info),
                )
            case _:
                pass

    async def transit_session_status(
        self,
        session_ids: Iterable[SessionId],
        status_changed_at: datetime | None = None,
        *,
        db_conn: Optional[SAConnection] = None,
    ) -> list[tuple[SessionRow, bool]]:
        if not session_ids:
            return []
        now = status_changed_at or datetime.now(tzutc())

        async def _transit(_db_conn: SAConnection) -> list[tuple[SessionRow, bool]]:
            result: list[tuple[SessionRow, bool]] = []
            for sid in session_ids:
                row, is_transited = await self._transit_session_status(_db_conn, sid, now)
                result.append((row, is_transited))
            for row, is_transited in result:
                if is_transited:
                    await self._post_status_transition(row)
            return result

        if db_conn is not None:
            return await _transit(db_conn)
        else:
            async with self.db.connect() as db_conn:
                return await _transit(db_conn)

    async def register_status_updatable_session(self, session_ids: Iterable[SessionId]) -> None:
        if not session_ids:
            return

        sadd_session_ids_script = textwrap.dedent("""
        local key = KEYS[1]
        local values = ARGV
        return redis.call('SADD', key, unpack(values))
        """)
        try:
            await redis_helper.execute_script(
                self.redis_obj,
                "session_status_update",
                sadd_session_ids_script,
                [self.status_set_key],
                [self._encoder(sid) for sid in session_ids],
            )
        except (
            redis.exceptions.RedisError,
            redis.exceptions.RedisClusterException,
            redis.exceptions.ChildDeadlockedError,
        ) as e:
            log.warning(f"Failed to update session status to redis, skip. (e:{repr(e)})")

    async def get_status_updatable_sessions(self) -> list[SessionId]:
        pop_all_session_id_script = textwrap.dedent("""
        local key = KEYS[1]
        local count = redis.call('SCARD', key)
        return redis.call('SPOP', key, count)
        """)
        try:
            raw_result = await redis_helper.execute_script(
                self.redis_obj,
                "pop_all_session_id_to_update_status",
                pop_all_session_id_script,
                [self.status_set_key],
                [],
            )
        except (
            redis.exceptions.RedisError,
            redis.exceptions.RedisClusterException,
            redis.exceptions.ChildDeadlockedError,
        ) as e:
            log.warning(f"Failed to fetch session status data from redis, skip. (e:{repr(e)})")
            return []
        raw_result = cast(list[bytes], raw_result)
        result: list[SessionId] = []
        for raw_session_id in raw_result:
            try:
                result.append(self._decoder(raw_session_id))
            except (ValueError, SyntaxError):
                log.warning(f"Cannot parse session id, skip. (id:{raw_session_id})")
                continue
        return result

    async def deregister_status_updatable_session(
        self,
        session_ids: Iterable[SessionId],
    ) -> int:
        if not session_ids:
            return 0

        srem_session_ids_script = textwrap.dedent("""
        local key = KEYS[1]
        local values = ARGV
        return redis.call('SREM', key, unpack(values))
        """)
        try:
            ret = await redis_helper.execute_script(
                self.redis_obj,
                "session_status_update",
                srem_session_ids_script,
                [self.status_set_key],
                [self._encoder(sid) for sid in session_ids],
            )
        except (
            redis.exceptions.RedisError,
            redis.exceptions.RedisClusterException,
            redis.exceptions.ChildDeadlockedError,
        ) as e:
            log.warning(f"Failed to remove session status data from redis, skip. (e:{repr(e)})")
            return 0
        return ret


class SessionDependencyRow(Base):
    __tablename__ = "session_dependencies"
    session_id = sa.Column(
        "session_id",
        GUID,
        sa.ForeignKey("sessions.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    depends_on = sa.Column(
        "depends_on",
        GUID,
        sa.ForeignKey("sessions.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    __table_args__ = (
        # constraint
        sa.PrimaryKeyConstraint("session_id", "depends_on", name="sess_dep_pk"),
    )


async def check_all_dependencies(
    db_session: SASession,
    sess_ctx: SessionRow,
) -> List[SessionRow]:
    j = sa.join(
        SessionDependencyRow,
        SessionRow,
        SessionDependencyRow.depends_on == SessionDependencyRow.session_id,
    )
    query = (
        sa.select(SessionRow.id, SessionRow.name, SessionRow.result)
        .select_from(j)
        .where(SessionDependencyRow.session_id == sess_ctx.id)
    )
    result = await db_session.execute(query)
    rows = result.scalars().all()
    pending_dependencies = [
        sess_row for sess_row in rows if sess_row.result != SessionResult.SUCCESS
    ]
    return pending_dependencies


DEFAULT_SESSION_ORDERING = [
    sa.desc(
        sa.func.greatest(
            SessionRow.created_at,
            SessionRow.terminated_at,
        )
    ),
]


class ComputeSession(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    # identity
    session_id = graphene.UUID()  # identical to `id`
    main_kernel_id = graphene.UUID()
    tag = graphene.String()
    name = graphene.String()
    type = graphene.String()
    main_kernel_role = graphene.String()
    priority = graphene.Int(
        description="Added in 24.09.0.",
    )

    # image
    image = graphene.String()  # image for the main container
    architecture = graphene.String()  # image architecture for the main container
    registry = graphene.String()  # image registry for the main container
    cluster_template = graphene.String()
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()

    # ownership
    domain_name = graphene.String()
    group_name = graphene.String()
    group_id = graphene.UUID()
    user_email = graphene.String()
    full_name = graphene.String()
    user_id = graphene.UUID()
    access_key = graphene.String()
    created_user_email = graphene.String()
    created_user_id = graphene.UUID()

    # status
    status = graphene.String()
    status_changed = GQLDateTime()
    status_info = graphene.String()
    status_data = graphene.JSONString()
    status_history = graphene.JSONString()
    created_at = GQLDateTime()
    terminated_at = GQLDateTime()
    starts_at = GQLDateTime()
    scheduled_at = GQLDateTime()
    startup_command = graphene.String()
    result = graphene.String()
    commit_status = graphene.String()
    abusing_reports = graphene.List(lambda: graphene.JSONString)
    idle_checks = graphene.JSONString()

    # resources
    agent_ids = graphene.List(lambda: graphene.String)
    agents = graphene.List(lambda: graphene.String)
    resource_opts = graphene.JSONString()
    scaling_group = graphene.String()
    service_ports = graphene.JSONString()
    mounts = graphene.List(lambda: graphene.String)
    vfolder_mounts = graphene.List(lambda: graphene.String)
    occupying_slots = graphene.JSONString()
    occupied_slots = graphene.JSONString()  # legacy
    requested_slots = graphene.JSONString(description="Added in 24.03.0.")

    # statistics
    num_queries = BigInt()

    # owned containers (aka kernels)
    containers = graphene.List(lambda: ComputeContainer)

    # relations
    dependencies = graphene.List(lambda: ComputeSession)

    inference_metrics = graphene.JSONString()

    @classmethod
    def parse_row(cls, ctx: GraphQueryContext, row: Row) -> Mapping[str, Any]:
        assert row is not None
        email = getattr(row, "email")
        full_name = getattr(row, "full_name")
        group_name = getattr(row, "group_name")
        row = row.SessionRow
        status_history = row.status_history or {}
        raw_scheduled_at = status_history.get(SessionStatus.SCHEDULED.name)
        return {
            # identity
            "id": row.id,
            "session_id": row.id,
            "main_kernel_id": row.main_kernel.id,
            "tag": row.tag,
            "name": row.name,
            "type": row.session_type.name,
            "main_kernel_role": row.session_type.name,  # legacy
            "priority": row.priority,
            # image
            "image": row.images[0] if row.images is not None else "",
            "architecture": row.main_kernel.architecture,
            "registry": row.main_kernel.registry,
            "cluster_template": None,  # TODO: implement
            "cluster_mode": row.cluster_mode,
            "cluster_size": row.cluster_size,
            # ownership
            "domain_name": row.domain_name,
            "group_name": group_name[0],
            "group_id": row.group_id,
            "user_email": email,
            "full_name": full_name,
            "user_id": row.user_uuid,
            "access_key": row.access_key,
            "created_user_email": None,  # TODO: implement
            "created_user_id": None,  # TODO: implement
            # status
            "status": row.status.name,
            "status_changed": row.status_changed,
            "status_info": row.status_info,
            "status_data": row.status_data,
            "status_history": status_history,
            "created_at": row.created_at,
            "terminated_at": row.terminated_at,
            "starts_at": row.starts_at,
            "scheduled_at": (
                datetime.fromisoformat(raw_scheduled_at) if raw_scheduled_at is not None else None
            ),
            "startup_command": row.startup_command,
            "result": row.result.name,
            # resources
            "agent_ids": row.agent_ids,
            "agents": row.agent_ids,  # for backward compatibility
            "scaling_group": row.scaling_group_name,
            "service_ports": row.main_kernel.service_ports,
            "mounts": [mount.name for mount in row.vfolder_mounts],
            "vfolder_mounts": row.vfolder_mounts,
            "occupying_slots": row.occupying_slots.to_json(),
            "occupied_slots": row.occupying_slots.to_json(),
            "requested_slots": row.requested_slots.to_json(),
            # statistics
            "num_queries": row.num_queries,
        }

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row | None) -> ComputeSession | None:
        if row is None:
            return None
        props = cls.parse_row(ctx, row)
        return cls(**props)

    async def resolve_inference_metrics(
        self, info: graphene.ResolveInfo
    ) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx, "KernelStatistics.inference_metrics_by_kernel"
        )
        return await loader.load(self.id)

    async def resolve_containers(
        self,
        info: graphene.ResolveInfo,
    ) -> Iterable[ComputeContainer]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "ComputeContainer.by_session")
        return await loader.load(self.session_id)

    async def resolve_dependencies(
        self,
        info: graphene.ResolveInfo,
    ) -> Iterable[ComputeSession]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "ComputeSession.by_dependency")
        return await loader.load(self.id)

    async def resolve_commit_status(self, info: graphene.ResolveInfo) -> str:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx, "ComputeSession.commit_statuses"
        )
        return await loader.load(self.main_kernel_id)

    async def resolve_resource_opts(self, info: graphene.ResolveInfo) -> dict[str, Any]:
        containers = self.containers
        if containers is None:
            containers = await self.resolve_containers(info)
        if containers is None:
            return {}
        self.containers = containers
        return {cntr.cluster_hostname: cntr.resource_opts for cntr in containers}

    async def resolve_abusing_reports(
        self, info: graphene.ResolveInfo
    ) -> Iterable[Optional[Mapping[str, Any]]]:
        containers = self.containers
        if containers is None:
            containers = await self.resolve_containers(info)
        if containers is None:
            return []
        self.containers = containers
        return [(await con.resolve_abusing_report(info, self.access_key)) for con in containers]

    async def resolve_idle_checks(self, info: graphene.ResolveInfo) -> Mapping[str, Any]:
        graph_ctx: GraphQueryContext = info.context
        return await graph_ctx.idle_checker_host.get_idle_check_report(self.session_id)

    _queryfilter_fieldspec: FieldSpecType = {
        "id": ("sessions_id", None),
        "type": ("sessions_session_type", enum_field_getter(SessionTypes)),
        "name": ("sessions_name", None),
        "priority": ("sessions_priority", None),
        "image": (ArrayFieldItem("sessions_images"), None),
        "agent_ids": (ArrayFieldItem("sessions_agent_ids"), None),
        "agent_id": (ArrayFieldItem("sessions_agent_ids"), None),
        "agents": (ArrayFieldItem("sessions_agent_ids"), None),  # for backward compatibility
        "domain_name": ("sessions_domain_name", None),
        "group_name": ("group_name", None),
        "user_email": ("users_email", None),
        "user_id": ("sessions_user_uuid", None),
        "full_name": ("users_full_name", None),
        "access_key": ("sessions_access_key", None),
        "scaling_group": ("sessions_scaling_group_name", None),
        "cluster_mode": ("sessions_cluster_mode", lambda s: ClusterMode[s]),
        "cluster_size": ("sessions_cluster_size", None),
        "status": ("sessions_status", enum_field_getter(SessionStatus)),
        "status_info": ("sessions_status_info", None),
        "result": ("sessions_result", enum_field_getter(SessionResult)),
        "created_at": ("sessions_created_at", dtparse),
        "terminated_at": ("sessions_terminated_at", dtparse),
        "starts_at": ("sessions_starts_at", dtparse),
        "scheduled_at": (
            JSONFieldItem("sessions_status_history", SessionStatus.SCHEDULED.name),
            dtparse,
        ),
        "startup_command": ("sessions_startup_command", None),
    }

    _queryorder_colmap: ColumnMapType = {
        "id": ("sessions_id", None),
        "type": ("sessions_session_type", None),
        "name": ("sessions_name", None),
        "image": ("sessions_images", None),
        "priority": ("sessions_priority", None),
        "agent_ids": ("sessions_agent_ids", None),
        "agent_id": ("sessions_agent_ids", None),
        "agents": ("sessions_agent_ids", None),
        "domain_name": ("sessions_domain_name", None),
        "group_name": ("group_name", None),
        "user_email": ("users_email", None),
        "user_id": ("sessions_user_uuid", None),
        "full_name": ("users_full_name", None),
        "access_key": ("sessions_access_key", None),
        "scaling_group": ("sessions_scaling_group_name", None),
        "cluster_mode": ("sessions_cluster_mode", None),
        # "cluster_template": "cluster_template",
        "cluster_size": ("sessions_cluster_size", None),
        "status": ("sessions_status", None),
        "status_info": ("sessions_status_info", None),
        "result": ("sessions_result", None),
        "created_at": ("sessions_created_at", None),
        "terminated_at": ("sessions_terminated_at", None),
        "starts_at": ("sessions_starts_at", None),
        "scheduled_at": (
            JSONFieldItem("sessions_status_history", SessionStatus.SCHEDULED.name),
            None,
        ),
    }

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[UUID] = None,
        access_key: Optional[str] = None,
        status: Optional[str] = None,
        filter: Optional[str] = None,
    ) -> int:
        if isinstance(status, str):
            status_list = [SessionStatus[s] for s in status.split(",")]
        elif isinstance(status, SessionStatus):
            status_list = [status]
        j = (
            # joins with GroupRow and UserRow do not need to be LEFT OUTER JOIN since those foreign keys are not nullable.
            sa.join(SessionRow, GroupRow, SessionRow.group_id == GroupRow.id)
            .join(UserRow, SessionRow.user_uuid == UserRow.uuid)
            .join(KernelRow, SessionRow.id == KernelRow.session_id)
        )
        query = sa.select([sa.func.count(sa.distinct(SessionRow.id))]).select_from(j)
        if domain_name is not None:
            query = query.where(SessionRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(SessionRow.group_id == group_id)
        if access_key is not None:
            query = query.where(SessionRow.access_key == access_key)
        if status is not None:
            query = query.where(SessionRow.status.in_(status_list))
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
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
        domain_name: Optional[str] = None,
        group_id: Optional[UUID] = None,
        access_key: Optional[str] = None,
        status: Optional[str] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[ComputeSession | None]:
        if status is None:
            status_list = None
        elif isinstance(status, str):
            status_list = [SessionStatus[s] for s in status.split(",")]
        elif isinstance(status, SessionStatus):
            status_list = [status]
        j = (
            # joins with GroupRow and UserRow do not need to be LEFT OUTER JOIN since those foreign keys are not nullable.
            sa.join(SessionRow, GroupRow, SessionRow.group_id == GroupRow.id).join(
                UserRow, SessionRow.user_uuid == UserRow.uuid
            )
        )
        query = (
            sa.select(
                SessionRow,
                agg_to_array(GroupRow.name).label("group_name"),
                UserRow.email,
                UserRow.full_name,
            )
            .select_from(j)
            .options(selectinload(SessionRow.kernels.and_(KernelRow.cluster_role == DEFAULT_ROLE)))
            .group_by(SessionRow, UserRow.email, UserRow.full_name)
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(SessionRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(SessionRow.group_id == group_id)
        if access_key is not None:
            query = query.where(SessionRow.access_key == access_key)
        if status is not None:
            query = query.where(SessionRow.status.in_(status_list))
        if filter is not None:
            parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = parser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(*DEFAULT_SESSION_ORDERING)
        async with ctx.db.begin_readonly_session() as db_sess:
            return [cls.from_row(ctx, r) async for r in (await db_sess.stream(query))]

    @classmethod
    async def batch_load_detail(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
        *,
        domain_name: Optional[str] = None,
        access_key: Optional[str] = None,
    ) -> Sequence[ComputeSession | None]:
        j = sa.join(SessionRow, GroupRow, SessionRow.group_id == GroupRow.id).join(
            UserRow, SessionRow.user_uuid == UserRow.uuid
        )
        query = (
            sa.select(
                SessionRow,
                GroupRow.name.label("group_name"),
                UserRow.email,
                UserRow.full_name,
            )
            .select_from(j)
            .where(SessionRow.id.in_(session_ids))
            .options(selectinload(SessionRow.kernels))
        )
        if domain_name is not None:
            query = query.where(SessionRow.domain_name == domain_name)
        if access_key is not None:
            query = query.where(SessionRow.access_key == access_key)
        async with ctx.db.begin_readonly_session() as db_sess:
            return await batch_result_in_session(
                ctx,
                db_sess,
                query,
                cls,
                session_ids,
                lambda row: row.SessionRow.id,
            )

    @classmethod
    async def batch_load_by_dependency(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Sequence[ComputeSession]]:
        j = sa.join(
            SessionRow,
            SessionDependencyRow,
            SessionRow.id == SessionDependencyRow.depends_on,
        )
        query = (
            sa.select(SessionRow)
            .select_from(j)
            .where(SessionDependencyRow.session_id.in_(session_ids))
            .options(selectinload(SessionRow.kernels))
        )
        async with ctx.db.begin_readonly_session() as db_sess:
            return await batch_multiresult_in_session(
                ctx,
                db_sess,
                query,
                cls,
                session_ids,
                lambda row: row.SessionRow.id,
            )

    @classmethod
    async def batch_load_commit_statuses(
        cls,
        ctx: GraphQueryContext,
        kernel_ids: Sequence[KernelId],
    ) -> Sequence[str]:
        commit_statuses = await ctx.registry.get_commit_status(kernel_ids)
        return [commit_statuses[kernel_id] for kernel_id in kernel_ids]


class ComputeSessionList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(ComputeSession, required=True)


class InferenceSession(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)


class InferenceSessionList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(InferenceSession, required=True)


ALL_COMPUTE_SESSION_PERMISSIONS: frozenset[ComputeSessionPermission] = frozenset([
    perm for perm in ComputeSessionPermission
])
OWNER_PERMISSIONS: frozenset[ComputeSessionPermission] = ALL_COMPUTE_SESSION_PERMISSIONS
ADMIN_PERMISSIONS: frozenset[ComputeSessionPermission] = ALL_COMPUTE_SESSION_PERMISSIONS
MONITOR_PERMISSIONS: frozenset[ComputeSessionPermission] = frozenset({
    ComputeSessionPermission.READ_ATTRIBUTE,
    ComputeSessionPermission.UPDATE_ATTRIBUTE,
})
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[ComputeSessionPermission] = frozenset()
MEMBER_PERMISSIONS: frozenset[ComputeSessionPermission] = frozenset()

WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)


class ComputeSessionPermissionContext(
    AbstractPermissionContext[ComputeSessionPermission, SessionRow, SessionId]
):
    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.user_id_to_permission_map:
            cond = _OR_coalesce(
                cond, SessionRow.user_uuid.in_(self.user_id_to_permission_map.keys())
            )
        if self.project_id_to_permission_map:
            cond = _OR_coalesce(
                cond, SessionRow.group_id.in_(self.project_id_to_permission_map.keys())
            )
        if self.domain_name_to_permission_map:
            cond = _OR_coalesce(
                cond, SessionRow.domain_name.in_(self.domain_name_to_permission_map.keys())
            )
        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, SessionRow.id.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, SessionRow.id.in_(self.object_id_to_overriding_permission_map.keys())
            )
        return cond

    async def build_query(self) -> sa.sql.Select | None:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(SessionRow).where(cond)

    async def calculate_final_permission(
        self, rbac_obj: SessionRow
    ) -> frozenset[ComputeSessionPermission]:
        session_row = rbac_obj
        session_id = cast(SessionId, session_row.id)
        permissions: frozenset[ComputeSessionPermission] = frozenset()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(session_id)
        ) is not None:
            permissions = overriding_perm
        else:
            permissions |= self.object_id_to_additional_permission_map.get(session_id, set())
            permissions |= self.user_id_to_permission_map.get(session_row.user_uuid, set())
            permissions |= self.project_id_to_permission_map.get(session_row.group_id, set())
            permissions |= self.domain_name_to_permission_map.get(session_row.domain_name, set())
        return permissions


class ComputeSessionPermissionContextBuilder(
    AbstractPermissionContextBuilder[ComputeSessionPermission, ComputeSessionPermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[ComputeSessionPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        permissions = await self._calculate_permission_by_predefined_roles(roles)
        return permissions

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> ComputeSessionPermissionContext:
        from .domain import DomainRow

        perm_ctx = ComputeSessionPermissionContext()
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
    ) -> ComputeSessionPermissionContext:
        permission_ctx = await self._build_at_domain_scope_non_recursively(ctx, scope.domain_name)
        _user_perm_ctx = await self._build_at_user_scope_in_domain(
            ctx, ctx.user_id, scope.domain_name
        )
        permission_ctx.merge(_user_perm_ctx)
        _project_perm_ctx = await self._build_at_project_scopes_in_domain(ctx, scope.domain_name)
        permission_ctx.merge(_project_perm_ctx)
        return permission_ctx

    @override
    async def build_ctx_in_project_scope(
        self,
        ctx: ClientContext,
        scope: ProjectScope,
    ) -> ComputeSessionPermissionContext:
        permission_ctx = await self._build_at_project_scope_non_recursively(ctx, scope.project_id)
        _user_perm_ctx = await self._build_at_user_scope_non_recursively(ctx, ctx.user_id)
        permission_ctx.merge(_user_perm_ctx)
        return permission_ctx

    @override
    async def build_ctx_in_user_scope(
        self,
        ctx: ClientContext,
        scope: UserRBACScope,
    ) -> ComputeSessionPermissionContext:
        return await self._build_at_user_scope_non_recursively(ctx, scope.user_id)

    async def _build_at_domain_scope_non_recursively(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> ComputeSessionPermissionContext:
        permissions = await self.calculate_permission(ctx, DomainScope(domain_name))
        result = ComputeSessionPermissionContext(
            domain_name_to_permission_map={domain_name: permissions}
        )
        return result

    async def _build_at_user_scope_in_domain(
        self,
        ctx: ClientContext,
        user_id: UUID,
        domain_name: str,
    ) -> ComputeSessionPermissionContext:
        # For Superadmin and monitor who can create objects in multiple different domains.
        permissions = await self.calculate_permission(ctx, UserRBACScope(user_id, domain_name))

        _vfolder_stmt = (
            sa.select(SessionRow)
            .where((SessionRow.user_uuid == user_id) & (SessionRow.domain_name == domain_name))
            .options(load_only(SessionRow.id))
        )
        own_folder_map = {
            row.id: permissions for row in await self.db_session.scalars(_vfolder_stmt)
        }
        result = ComputeSessionPermissionContext(
            object_id_to_additional_permission_map=own_folder_map
        )
        return result

    async def _build_at_project_scopes_in_domain(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> ComputeSessionPermissionContext:
        result = ComputeSessionPermissionContext()

        _project_stmt = (
            sa.select(GroupRow)
            .where(GroupRow.domain_name == domain_name)
            .options(load_only(GroupRow.id))
        )
        for row in await self.db_session.scalars(_project_stmt):
            _row = cast(GroupRow, row)
            _project_perm_ctx = await self._build_at_project_scope_non_recursively(ctx, _row.id)
            result.merge(_project_perm_ctx)
        return result

    async def _build_at_project_scope_non_recursively(
        self,
        ctx: ClientContext,
        project_id: UUID,
    ) -> ComputeSessionPermissionContext:
        permissions = await self.calculate_permission(ctx, ProjectScope(project_id))
        result = ComputeSessionPermissionContext(
            project_id_to_permission_map={project_id: permissions}
        )
        return result

    async def _build_at_user_scope_non_recursively(
        self,
        ctx: ClientContext,
        user_id: UUID,
    ) -> ComputeSessionPermissionContext:
        permissions = await self.calculate_permission(ctx, UserRBACScope(user_id))
        result = ComputeSessionPermissionContext(user_id_to_permission_map={user_id: permissions})
        return result

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[ComputeSessionPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[ComputeSessionPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[ComputeSessionPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[ComputeSessionPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[ComputeSessionPermission]:
        return MEMBER_PERMISSIONS


async def get_permission_ctx(
    db_conn: SAConnection,
    ctx: ClientContext,
    target_scope: ScopeType,
    requested_permission: ComputeSessionPermission,
) -> ComputeSessionPermissionContext:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        builder = ComputeSessionPermissionContextBuilder(db_session)
        permission_ctx = await builder.build(ctx, target_scope, requested_permission)
    return permission_ctx
