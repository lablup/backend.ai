from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Mapping, Sequence
from uuid import UUID

from dateutil.tz import tzutc
from pydantic import Field

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
    VFolderMount,
)

from ..exceptions import convert_to_status_data
from ..models.session import (
    SESSION_STATUS_TRANSITION_MAP,
    SessionRow,
    SessionStatus,
    determine_session_status,
)
from ..models.utils import sql_json_increment, sql_json_merge
from .base import (
    BaseCreationSchema,
    BaseQuerySchema,
)
from .context import DBContext
from .kernel import KernelMutation, PendingKernel, PickedKernel, ScheduledKernel

if TYPE_CHECKING:
    from ..api.exceptions import InstanceNotAvailable
    from ..scheduler.types import KernelAgentBinding


class Session(BaseCreationSchema):
    id: SessionId
    creation_id: str
    name: str
    session_type: SessionTypes = SessionTypes.INTERACTIVE
    cluster_mode: str
    cluster_size: int = 1

    # Resource ownership
    scaling_group_name: str | None
    target_sgroup_names: list[str]
    domain_name: str
    group_id: UUID
    user_uuid: UUID
    access_key: str
    tag: str | None

    # Resource occupation
    occupying_slots: ResourceSlot = Field(default_factory=ResourceSlot)
    requested_slots: ResourceSlot = Field(default_factory=ResourceSlot)
    vfolder_mounts: list[VFolderMount]
    environ: dict
    bootstrap_script: str | None
    use_host_network: bool = False

    # Lifecycle
    timeout: int | None
    created_at: datetime | None
    terminated_at: datetime | None
    starts_at: datetime | None
    status: SessionStatus = SessionStatus.PENDING
    status_info: str | None
    status_data: dict
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
    #   "session": {
    #     // termination info for the session
    #     "status": "terminating" | "terminated"
    #         // "terminated" means all kernels that belong to the same session has terminated.
    #         // used to prevent duplication of SessionTerminatedEvent
    #   }
    # }
    status_history: dict
    callback_url: str | None

    startup_command: str | None
    result: SessionResult = SessionResult.UNDEFINED

    # Resource metrics measured upon termination
    num_queries: int = 0
    last_stat: dict


class PendingSession(BaseQuerySchema):
    id: SessionId
    creation_id: str
    name: str
    session_type: SessionTypes
    access_key: AccessKey

    kernels: list[PendingKernel]

    @property
    def is_private(self) -> bool:
        return any([kernel.is_private for kernel in self.kernels])

    @property
    def main_kernel(self) -> PendingKernel:
        kerns = tuple(kern for kern in self.kernels if kern.is_main)
        if len(kerns) > 1:
            raise RuntimeError(
                f"Session (id: {self.id}) has more than 1 main kernel.",
            )
        if len(kerns) == 0:
            raise RuntimeError(
                f"Session (id: {self.id}) has no main kernel.",
            )
        return kerns[0]


class PickedSession(BaseQuerySchema):
    id: SessionId
    creation_id: str
    name: str
    session_type: SessionTypes
    access_key: AccessKey
    cluster_mode: ClusterMode
    cluster_size: int
    domain_name: str
    group_id: UUID
    status_data: dict[str, Any]
    scaling_group: str
    resource_policy: str
    resource_opts: dict[str, Any]
    requested_slots: ResourceSlot
    target_sgroup_names: list[str]
    environ: dict[str, str]
    vfolder_mounts: list[VFolderMount]
    bootstrap_script: str | None
    startup_command: str | None
    internal_data: dict | None
    preopen_ports: list[int]
    created_at: datetime
    use_host_network: bool

    kernels: list[PickedKernel]

    @property
    def is_private(self) -> bool:
        return any([kernel.is_private for kernel in self.kernels])

    @property
    def main_kernel(self) -> PickedKernel:
        kerns = tuple(kern for kern in self.kernels if kern.is_main)
        if len(kerns) > 1:
            raise RuntimeError(
                f"Session (id: {self.id}) has more than 1 main kernel.",
            )
        if len(kerns) == 0:
            raise RuntimeError(
                f"Session (id: {self.id}) has no main kernel.",
            )
        return kerns[0]


class ExistingSession(BaseQuerySchema):
    id: SessionId
    access_key: AccessKey
    occupying_slots: ResourceSlot


class ScheduledSession(BaseQuerySchema):
    id: SessionId
    creation_id: str
    name: str
    access_key: AccessKey
    session_type: SessionTypes
    scaling_group_name: str
    use_host_network: bool
    cluster_mode: ClusterMode
    cluster_size: int
    vfolder_mounts: list[VFolderMount]

    environ: dict

    kernels: list[ScheduledKernel]

    @property
    def main_kernel(self) -> ScheduledKernel:
        kerns = tuple(kern for kern in self.kernels if kern.is_main)
        if len(kerns) > 1:
            raise RuntimeError(
                f"Session (id: {self.id}) has more than 1 main kernel.",
            )
        if len(kerns) == 0:
            raise RuntimeError(
                f"Session (id: {self.id}) has no main kernel.",
            )
        return kerns[0]


class SessionMutation:
    @staticmethod
    async def cancel_sessions(
        db: DBContext,
        session_ids: Sequence[SessionId],
        reason: str = "pending-timeout",
        exc: Exception | None = None,
        *,
        is_debug: bool = False,
    ) -> None:
        now = datetime.now(tzutc())
        exc_data = convert_to_status_data(exc, is_debug) if exc is not None else None
        await SessionRow.set_status(
            db.sa_engine,
            session_ids,
            SessionStatus.CANCELLED,
            status_data=exc_data,
            status_changed_at=now,
            reason=reason,
        )
        await KernelMutation.mark_cancelled(
            db, session_ids, reason, status_data=exc_data, status_changed_at=now
        )

    @staticmethod
    async def mark_terminating(
        db: DBContext,
        session_ids: Sequence[SessionId],
    ) -> None:
        await SessionRow.set_status(
            db.sa_engine,
            session_ids,
            SessionStatus.TERMINATING,
        )

    @staticmethod
    async def cancel_predicate_failed_session(
        db: DBContext,
        session_id: SessionId,
        status_data: dict[str, Any],
        status_info: str = "predicate-checks-failed",
    ) -> None:
        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            status_data=sql_json_increment(
                SessionRow.status_data,
                ("scheduler", "retries"),
                parent_updates=status_data,
            ),
            reason=status_info,
        )

    @staticmethod
    async def update_passed_predicate(
        db: DBContext,
        session_ids: Sequence[SessionId],
        status_data: Mapping[str, Any],
    ) -> None:
        await SessionRow.set_status(
            db.sa_engine,
            session_ids,
            status_data=sql_json_merge(
                SessionRow.status_data,
                ("scheduler",),
                obj=status_data,
            ),
        )

    @staticmethod
    async def update_instance_not_available(
        db: DBContext,
        session_id: SessionId,
        exc: InstanceNotAvailable,
    ) -> None:
        now = datetime.now(tzutc())
        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            reason="no-available-instances",
            status_data=sql_json_increment(
                SessionRow.status_data,
                ("scheduler", "retries"),
                parent_updates={
                    "last_try": now.isoformat(),
                    "msg": exc.extra_msg,
                },
            ),
            status_changed_at=now,
        )

    @staticmethod
    async def update_schedule_generic_failure(
        db: DBContext,
        session_id: SessionId,
        exc: Exception,
        is_debug: bool = False,
    ) -> None:
        exc_data = convert_to_status_data(exc, is_debug)
        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            reason="scheduler-error",
            status_data=exc_data,
        )

    @staticmethod
    async def finalize_scheduled(
        db: DBContext,
        session_id: SessionId,
        kernel_agent_bindings: Sequence[KernelAgentBinding],
    ) -> None:
        now = datetime.now(tzutc())
        for binding in kernel_agent_bindings:
            kernel = binding.kernel
            agent_id = binding.agent_alloc_ctx.agent_id
            agent_addr = binding.agent_alloc_ctx.agent_addr
            assert agent_id is not None
            await KernelMutation.finalize_scheduled(db, kernel.id, agent_id, agent_addr, now)
        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            SessionStatus.SCHEDULED,
            reason="scheduled",
            status_changed_at=now,
        )

    @staticmethod
    async def mark_preparing(db: DBContext, session_ids: Sequence[SessionId]) -> None:
        now = datetime.now(tzutc())
        await SessionRow.set_status(
            db.sa_engine,
            session_ids,
            SessionStatus.PREPARING,
            status_changed_at=now,
        )
        await KernelMutation.mark_preparing(db, session_ids, now)

    @staticmethod
    async def mark_restarting(db: DBContext, session_id: SessionId) -> None:
        now = datetime.now(tzutc())
        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            SessionStatus.RESTARTING,
            status_changed_at=now,
        )
        await KernelMutation.mark_restarting(db, session_id, now)

    @classmethod
    async def transit_status(cls, db: DBContext, session_id: SessionId) -> SessionRow | None:
        session = await SessionRow.get_session_to_determine_status(db.sa_engine, session_id)
        determined_status = determine_session_status(session.kernels)
        if determined_status not in SESSION_STATUS_TRANSITION_MAP[session.status]:
            return None

        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            determined_status,
        )
        async with db.sa_engine.begin_readonly_session() as db_sess:
            return await SessionRow.get_session_by_id(db_sess, session_id)
