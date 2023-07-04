from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Mapping, Sequence
from uuid import UUID

from dateutil.tz import tzutc
from pydantic import BaseModel, Field

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
from ..models.session import SessionStatus
from .base import (
    BaseQuerySchema,
    BaseSchema,
    ToNullableFields,
)
from .context import DBContext
from .kernel import KernelMutationArgs, KernelQuery, PendingKernel, PickedKernel, ScheduledKernel

if TYPE_CHECKING:
    from ..api.exceptions import InstanceNotAvailable
    from ..models.session import SessionRow
    from ..scheduler.types import KernelAgentBinding


class Session(BaseSchema):
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


class SessionWithKernels(BaseQuerySchema):
    id: SessionId
    kernels: list[KernelQuery]

    @property
    def main_kernel(self) -> KernelQuery:
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


class SessionQuery(Session, metaclass=ToNullableFields):
    @classmethod
    async def by_status(cls, db: DBContext, status: SessionStatus) -> list[SessionQuery]:
        from ..models.session import SessionRow

        rows = await SessionRow.get_session_by_status(db.sa_engine, status, with_kernels=True)
        return [SessionQuery.from_orm(row) for row in rows]


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


class SessionCreation(Session):
    id: SessionId | None  # type: ignore[assignment]


class SessionMutationArgs(BaseModel):
    status: SessionStatus | None = None
    status_data: Mapping[str, Any] | None = None
    status_info: str | None = None
    occupying_slots: ResourceSlot | None = None
    scaling_group: str | None = None

    @property
    def value_dict(self) -> dict[str, Any]:
        return self.dict(exclude_unset=True, exclude_none=True)


class SessionMutation:
    @staticmethod
    async def cancel_sessions(
        db: DBContext,
        session_ids: Sequence[SessionId],
        reason: str = "pending-timeout",
        exc: Exception | None = None,
        is_debug: bool = False,
    ) -> None:
        from ..models.kernel import KernelRow, KernelStatus
        from ..models.session import SessionRow

        now = datetime.now(tzutc())
        if exc is not None:
            exc_data = convert_to_status_data(exc, is_debug)
        await SessionRow.set_status(
            db.sa_engine,
            session_ids,
            SessionStatus.CANCELLED,
            status_data={**exc_data},
            status_changed_at=now,
            reason=reason,
        )
        args = KernelMutationArgs(
            status=KernelStatus.CANCELLED,
            status_info=reason,
            status_data=exc_data,
        )
        await KernelRow.set_status_by_session_id(
            db.sa_engine,
            session_ids,
            args,
            status_changed_at=now,
        )

    @staticmethod
    async def mark_terminating(
        db: DBContext,
        session_ids: Sequence[SessionId],
    ) -> None:
        from ..models.session import SessionRow

        now = datetime.now(tzutc())
        await SessionRow.set_status(
            db.sa_engine,
            session_ids,
            SessionStatus.TERMINATING,
            status_changed_at=now,
        )

    @staticmethod
    async def cancel_predicate_failed_session(
        db: DBContext,
        session_id: SessionId,
        status_data: dict[str, Any],
        status_info: str = "predicate-checks-failed",
    ) -> None:
        from ..models.session import SessionRow
        from ..models.utils import sql_json_increment

        now = datetime.now(tzutc())
        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            status_data=sql_json_increment(
                SessionRow.status_data,
                ("scheduler", "retries"),
                parent_updates=status_data,
            ),
            reason=status_info,
            status_changed_at=now,
        )

    @staticmethod
    async def update_passed_predicate(
        db: DBContext,
        session_ids: Sequence[SessionId],
        status_data: Mapping[str, Any],
    ) -> None:
        from ..models.kernel import KernelRow
        from ..models.session import SessionRow
        from ..models.utils import sql_json_merge

        await SessionRow.set_status(
            db.sa_engine,
            session_ids,
            status_data=sql_json_merge(
                KernelRow.status_data,
                ("scheduler",),
                obj=status_data,
            ),
        )
        args = KernelMutationArgs(
            status_data=sql_json_merge(
                SessionRow.status_data,
                ("scheduler",),
                obj=status_data,
            ),
        )
        await KernelRow.set_status_by_session_id(
            db.sa_engine,
            session_ids,
            args,
        )

    @staticmethod
    async def update_schedule_failure(
        db: DBContext,
        session_id: SessionId,
        exc: InstanceNotAvailable,
    ) -> None:
        from ..models.session import SessionRow
        from ..models.utils import sql_json_increment

        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            reason="no-available-instances",
            status_data=sql_json_increment(
                SessionRow.status_data,
                ("scheduler", "retries"),
                parent_updates={
                    "last_try": datetime.now(tzutc()).isoformat(),
                    "msg": exc.extra_msg,
                },
            ),
        )

    @staticmethod
    async def update_schedule_generic_failure(
        db: DBContext,
        session_id: SessionId,
        exc: Exception,
        is_debug: bool = False,
    ) -> None:
        from ..models.session import SessionRow

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
        from ..models.kernel import KernelRow, KernelStatus
        from ..models.session import SessionRow

        now = datetime.now(tzutc())
        for binding in kernel_agent_bindings:
            kernel = binding.kernel
            agent_id = binding.agent_alloc_ctx.agent_id
            agent_addr = binding.agent_alloc_ctx.agent_addr
            args = KernelMutationArgs(
                status=KernelStatus.SCHEDULED,
                agent=agent_id,
                agent_addr=agent_addr,
            )
            await KernelRow.set_status_by_kernel_id(
                db.sa_engine,
                (kernel.id,),
                args,
                status_changed_at=now,
            )
        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            SessionStatus.SCHEDULED,
            reason="scheduled",
            status_changed_at=now,
        )

    @staticmethod
    async def mark_preparing(db: DBContext, session_ids: Sequence[SessionId]) -> None:
        from ..models.kernel import KernelRow, KernelStatus
        from ..models.session import SessionRow

        now = datetime.now(tzutc())
        await SessionRow.set_status(
            db.sa_engine,
            session_ids,
            SessionStatus.PREPARING,
            status_changed_at=now,
        )
        args = KernelMutationArgs(status=KernelStatus.PREPARING)
        await KernelRow.set_status_by_session_id(
            db.sa_engine,
            session_ids,
            args,
            status_changed_at=now,
        )

    @staticmethod
    async def mark_restarting(db: DBContext, session_id: SessionId) -> None:
        from ..models.kernel import KernelRow, KernelStatus
        from ..models.session import SessionRow

        now = datetime.now(tzutc())
        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            SessionStatus.RESTARTING,
            status_changed_at=now,
        )
        args = KernelMutationArgs(status=KernelStatus.RESTARTING)
        await KernelRow.set_status_by_session_id(
            db.sa_engine,
            (session_id,),
            args,
            status_changed_at=now,
        )

    @classmethod
    async def transit_status(cls, db: DBContext, session_id: SessionId) -> SessionRow | None:
        from ..models.session import (
            SESSION_STATUS_TRANSITION_MAP,
            SessionRow,
            determine_session_status,
        )

        now = datetime.now(tzutc())

        session = await SessionRow.get_session_to_determine_status(db.sa_engine, session_id)
        determined_status = determine_session_status(session.kernels)
        if determined_status not in SESSION_STATUS_TRANSITION_MAP[session.status]:
            return None

        await SessionRow.set_status(
            db.sa_engine,
            (session_id,),
            determined_status,
            status_changed_at=now,
        )
        return session


class SessionCreationSchema(Session):
    pass
