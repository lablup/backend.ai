from __future__ import annotations

import asyncio
import enum
import logging
from collections.abc import Iterable, Mapping, Sequence
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    List,
    Optional,
    Union,
    cast,
)
from uuid import UUID

import aiotools
import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, noload, relationship, selectinload

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelId,
    SessionId,
    SessionResult,
    SessionTypes,
    VFolderMount,
)

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
    StructuredJSONObjectListColumn,
    URLColumn,
    batch_multiresult_in_session,
    batch_result_in_session,
)
from .group import GroupRow
from .kernel import ComputeContainer, KernelRow, KernelStatus
from .minilang import ArrayFieldItem, JSONFieldItem
from .minilang.ordering import ColumnMapType, QueryOrderParser
from .minilang.queryfilter import FieldSpecType, QueryFilterParser, enum_field_getter
from .user import UserRow
from .utils import (
    ExtendedAsyncSAEngine,
    JSONCoalesceExpr,
    agg_to_array,
    execute_with_retry,
    sql_json_merge,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = (
    "determine_session_status",
    "handle_session_exception",
    "SessionStatus",
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


class SessionStatus(enum.Enum):
    # values are only meaningful inside the manager
    PENDING = 0
    # ---
    SCHEDULED = 5
    # manager can set PENDING and SCHEDULED independently
    # ---
    PULLING = 9
    PREPARING = 10
    # ---
    RUNNING = 30
    RESTARTING = 31
    RUNNING_DEGRADED = 32
    # ---
    TERMINATING = 40
    TERMINATED = 41
    ERROR = 42
    CANCELLED = 43


FOLLOWING_SESSION_STATUSES = (
    # Session statuses that need to wait all sibling kernel
    SessionStatus.RUNNING,
    SessionStatus.TERMINATED,
)
LEADING_SESSION_STATUSES = (
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
        SessionStatus.TERMINATING,
        SessionStatus.TERMINATED,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.SCHEDULED: {
        SessionStatus.PULLING,
        SessionStatus.PREPARING,
        SessionStatus.TERMINATED,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.PULLING: {
        SessionStatus.PREPARING,
        SessionStatus.RUNNING,
        SessionStatus.RUNNING_DEGRADED,
        # SessionStatus.TERMINATING,  # cannot destroy PULLING session by user
        SessionStatus.TERMINATED,
        SessionStatus.ERROR,
        SessionStatus.CANCELLED,
    },
    SessionStatus.PREPARING: {
        SessionStatus.PULLING,
        SessionStatus.RUNNING,
        SessionStatus.RUNNING_DEGRADED,
        SessionStatus.TERMINATING,
        SessionStatus.TERMINATED,
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
    SessionStatus.ERROR: {SessionStatus.TERMINATED},
    SessionStatus.CANCELLED: set(),
}


def determine_session_status(sibling_kernels: Sequence[KernelRow]) -> SessionStatus:
    try:
        main_kern_status = [k.status for k in sibling_kernels if k.cluster_role == DEFAULT_ROLE][0]
    except IndexError:
        raise MainKernelNotFound("Cannot determine session status without status of main kernel")
    candidate: SessionStatus = KERNEL_SESSION_STATUS_MAPPING[main_kern_status]
    if candidate in LEADING_SESSION_STATUSES:
        return candidate
    for k in sibling_kernels:
        match candidate:
            case SessionStatus.RUNNING:
                match k.status:
                    case (
                        KernelStatus.PENDING
                        | KernelStatus.SCHEDULED
                        | KernelStatus.SUSPENDED
                        | KernelStatus.TERMINATED
                        | KernelStatus.CANCELLED
                    ):
                        # should not be it
                        pass
                    case KernelStatus.BUILDING:
                        continue
                    case KernelStatus.PULLING:
                        candidate = SessionStatus.PULLING
                    case KernelStatus.PREPARING:
                        candidate = SessionStatus.PREPARING
                    case KernelStatus.RUNNING | KernelStatus.RESTARTING | KernelStatus.RESIZING:
                        continue
                    case KernelStatus.TERMINATING | KernelStatus.ERROR:
                        candidate = SessionStatus.RUNNING_DEGRADED
            case SessionStatus.TERMINATED:
                match k.status:
                    case KernelStatus.PENDING | KernelStatus.CANCELLED:
                        # should not be it
                        pass
                    case (
                        KernelStatus.SCHEDULED
                        | KernelStatus.PREPARING
                        | KernelStatus.BUILDING
                        | KernelStatus.PULLING
                        | KernelStatus.RUNNING
                        | KernelStatus.RESTARTING
                        | KernelStatus.RESIZING
                        | KernelStatus.SUSPENDED
                    ):
                        pass
                    case KernelStatus.TERMINATING:
                        candidate = SessionStatus.TERMINATING
                    case KernelStatus.TERMINATED:
                        continue
                    case KernelStatus.ERROR:
                        return SessionStatus.ERROR
            case SessionStatus.RUNNING_DEGRADED:
                match k.status:
                    case (
                        KernelStatus.PENDING
                        | KernelStatus.SCHEDULED
                        | KernelStatus.PREPARING
                        | KernelStatus.BUILDING
                        | KernelStatus.PULLING
                        | KernelStatus.RESIZING
                        | KernelStatus.SUSPENDED
                        | KernelStatus.CANCELLED
                    ):
                        # should not be it
                        pass
                    case (
                        KernelStatus.RUNNING
                        | KernelStatus.RESTARTING
                        | KernelStatus.ERROR
                        | KernelStatus.TERMINATING
                    ):
                        continue
            case _:
                break
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
            self.compute_concurrency_used_key: len(self.compute_concurrency_used_key),
            self.system_concurrency_used_key: len(self.system_concurrency_used_key),
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


class SessionRow(Base):
    __tablename__ = "sessions"
    id = SessionIDColumn()
    creation_id = sa.Column("creation_id", sa.String(length=32), unique=False, index=False)
    name = sa.Column("name", sa.String(length=64), unique=False, index=True)
    session_type = sa.Column(
        "session_type",
        EnumType(SessionTypes),
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
    created_at = sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
    )
    terminated_at = sa.Column(
        "terminated_at", sa.DateTime(timezone=True), nullable=True, default=sa.null(), index=True
    )
    starts_at = sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True, default=sa.null())
    status = sa.Column(
        "status",
        EnumType(SessionStatus),
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
        sa.Index("ix_sessions_vfolder_mounts", vfolder_mounts, postgresql_using="gin"),
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
        return any([kernel.is_private for kernel in self.kernels])

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
    async def transit_session_status(
        cls,
        db: ExtendedAsyncSAEngine,
        session_id: SessionId,
        *,
        status_info: str | None = None,
    ) -> SessionStatus | None:
        """
        Check status of session's sibling kernels and transit the status of session.
        Return the new status of session.
        """
        now = datetime.now(tzutc())

        async def _check_and_update() -> SessionStatus | None:
            async with db.begin_session() as db_session:
                session_query = (
                    sa.select(SessionRow)
                    .where(SessionRow.id == session_id)
                    .with_for_update()
                    .options(
                        noload("*"),
                        load_only(SessionRow.status),
                        selectinload(SessionRow.kernels).options(
                            noload("*"), load_only(KernelRow.status, KernelRow.cluster_role)
                        ),
                    )
                )
                session_row: SessionRow = (await db_session.scalars(session_query)).first()
                determined_status = determine_session_status(session_row.kernels)
                if determined_status not in SESSION_STATUS_TRANSITION_MAP[session_row.status]:
                    # TODO: log or raise error
                    return None

                update_values = {
                    "status": determined_status,
                    "status_history": sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {
                            determined_status.name: now.isoformat(),
                        },
                    ),
                }
                if determined_status in (SessionStatus.CANCELLED, SessionStatus.TERMINATED):
                    update_values["terminated_at"] = now
                if status_info is not None:
                    update_values["status_info"] = status_info
                update_query = (
                    sa.update(SessionRow).where(SessionRow.id == session_id).values(**update_values)
                )
                await db_session.execute(update_query)
            return determined_status

        return await execute_with_retry(_check_and_update)

    @classmethod
    async def get_session_to_determine_status(
        cls, db_session: SASession, session_id: SessionId
    ) -> SessionRow:
        stmt = (
            sa.select(SessionRow)
            .where(SessionRow.id == session_id)
            .options(
                selectinload(SessionRow.kernels).options(
                    load_only(KernelRow.status, KernelRow.cluster_role, KernelRow.status_info)
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

        determined_status = determine_session_status(self.kernels)
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
        self.status_history = sql_json_merge(
            SessionRow.status_history,
            (),
            {
                status.name: now.isoformat(),
            },
        )
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
        max_matches: int = 10,
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
            "main_kernel_role": row.main_kernel.role.name,
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
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> ComputeSession | None:
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
        domain_name: str = None,
        access_key: str = None,
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
