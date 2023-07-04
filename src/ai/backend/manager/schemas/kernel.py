from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncGenerator, Mapping, Sequence
from uuid import UUID

from dateutil.tz import tzutc
from pydantic import BaseModel, Field

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.docker import ImageRef
from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ContainerId,
    DeviceModelInfo,
    DeviceName,
    KernelId,
    ResourceSlot,
    ServicePort,
    SessionId,
    SessionResult,
    SessionTypes,
    VFolderMount,
)

from ..defs import DEFAULT_ROLE
from ..models.kernel import PRIVATE_KERNEL_ROLES, KernelRole, KernelRow, KernelStatus
from ..models.utils import sql_json_merge
from .base import (
    BaseQuerySchema,
    BaseSchema,
    ToNullableFields,
)
from .context import DBContext


class Kernel(BaseSchema):
    id: KernelId
    session_id: SessionId
    session_creation_id: str
    session_name: str
    session_type: SessionTypes = SessionTypes.INTERACTIVE
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    cluster_size: int = 1
    cluster_role: str
    cluster_idx: int = 0
    local_rank: int = 0
    cluster_hostname: str

    # Resource ownership
    scaling_group: str | None
    agent: str | None
    agent_addr: str | None
    domain_name: str
    group_id: UUID
    user_uuid: UUID
    access_key: str
    image: str
    architecture: str = "x86_64"
    registry: str
    tag: str | None

    # Resource occupation
    container_id: str
    occupied_slots: ResourceSlot = Field(default_factory=ResourceSlot)
    requested_slots: ResourceSlot = Field(default_factory=ResourceSlot)
    environ: list[str] | None
    vfolder_mounts: list[VFolderMount] | None
    attached_devices: dict = Field(default_factory=dict)
    resource_opts: dict = Field(default_factory=dict)
    bootstrap_script: str | None
    # Port mappings
    # If kernel_host is NULL, it is assumed to be same to the agent host or IP.
    kernel_host: str | None
    repl_in_port: int
    repl_out_port: int
    service_ports: dict | None
    preopen_ports: list[int] | None
    use_host_network: bool = False

    # Lifecycle
    created_at: datetime | None
    terminated_at: datetime | None
    starts_at: datetime | None
    status: KernelStatus = KernelStatus.PENDING
    role: KernelRole = KernelRole.COMPUTE
    status_changed: datetime | None
    status_info: str | None
    # status_info contains a kebab-cased string that expresses a summary of the last status change.
    # Examples: "user-requested", "self-terminated", "predicate-checks-failed", "no-available-instances"
    status_data: dict | None
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
    # }
    status_history: dict | None
    callback_url: str | None
    startup_command: str | None
    result: SessionResult = SessionResult.UNDEFINED
    internal_data: dict | None
    container_log: str | None
    # Resource metrics measured upon termination
    num_queries: int = 0
    last_stat: dict | None


class KernelQuery(Kernel, metaclass=ToNullableFields):
    @property
    def is_main(self) -> bool:
        return self.cluster_role == DEFAULT_ROLE


class CreatedKernel(BaseQuerySchema):
    status: KernelStatus
    service_ports: dict
    role: KernelRole

    @staticmethod
    async def to_respond(db: DBContext, session_id: SessionId) -> list[CreatedKernel]:
        return [
            CreatedKernel.from_orm(row)
            for row in (await KernelRow.get_by_session_id(db.sa_engine, session_id))
        ]


class PendingKernel(BaseQuerySchema):
    id: KernelId
    role: KernelRole
    cluster_role: ClusterMode

    @property
    def is_private(self) -> bool:
        return self.role in PRIVATE_KERNEL_ROLES

    @property
    def is_main(self) -> bool:
        return self.cluster_role == DEFAULT_ROLE


class PickedKernel(BaseQuerySchema):
    id: KernelId
    role: KernelRole
    architecture: str
    session_id: SessionId
    access_key: AccessKey
    agent_id: AgentId | None
    agent_addr: str
    cluster_role: ClusterMode
    cluster_idx: int
    local_rank: int
    cluster_hostname: str
    image_ref: ImageRef
    resource_opts: dict
    requested_slots: ResourceSlot
    bootstrap_script: str | None
    startup_command: str | None
    created_at: datetime

    # agent: AgentQuery

    @property
    def is_private(self) -> bool:
        return self.role in PRIVATE_KERNEL_ROLES

    @property
    def is_main(self) -> bool:
        return self.cluster_role == DEFAULT_ROLE


class ScheduledKernel(BaseQuerySchema):
    id: KernelId
    agent_id: AgentId
    cluster_role: ClusterMode
    agent_addr: str
    container_id: str
    preopen_ports: list[int]
    internal_data: dict

    @property
    def is_main(self) -> bool:
        return self.cluster_role == DEFAULT_ROLE


class KernelResource(BaseQuerySchema):
    id: KernelId
    session_id: SessionId
    access_key: str
    role: KernelRole
    agent: AgentId
    agent_addr: str
    occupied_slots: ResourceSlot

    @staticmethod
    async def by_statuses(
        db: DBContext, statuses: Sequence[KernelStatus], agent_id: AgentId | None = None
    ) -> list[KernelResource]:
        return [
            KernelResource.from_orm(row)
            for row in (await KernelRow.get_kernel_by_status(db.sa_engine, statuses, agent_id))
        ]

    @staticmethod
    async def stream_by_statuses(
        db: DBContext, statuses: Sequence[KernelStatus], agent_id: AgentId | None = None
    ) -> AsyncGenerator[list[KernelResource], None]:
        async for rows in KernelRow.stream_kernel_by_status(db.sa_engine, statuses, agent_id):
            yield [KernelResource.from_orm(row) for row in rows]


class KernelMutationArgs(BaseModel):
    status: KernelStatus | None = None
    status_data: Mapping[str, Any] | None = None
    status_info: str | KernelLifecycleEventReason | None = None
    occupied_slots: ResourceSlot | None = None
    scaling_group: str | None = None
    container_id: ContainerId | None = None
    attached_devices: Mapping[DeviceName, list[DeviceModelInfo]] | None = None
    kernel_host: str | None = None
    repl_in_port: str | None = None
    repl_out_port: str | None = None
    stdin_port: str | None = None  # legacy
    stdout_port: str | None = None  # legacy
    service_ports: Sequence[ServicePort] | None = None
    agent: AgentId | None = None
    agent_addr: str | None = None
    last_stat: dict | None = None

    @property
    def value_dict(self) -> dict[str, Any]:
        return self.dict(exclude_unset=True, exclude_none=True)


class KernelMutation:
    @staticmethod
    async def update_failure(db: DBContext, kernel_ids: Sequence[KernelId], ex: Exception) -> None:
        now = datetime.now(tzutc())
        arg = KernelMutationArgs(
            status=KernelStatus.ERROR,
            status_info=f"other-error ({ex!r})",
        )
        await KernelRow.set_status_by_kernel_id(
            db.sa_engine,
            kernel_ids,
            arg,
            status_changed_at=now,
        )

    @staticmethod
    async def mark_terminating(
        db: DBContext,
        kernel_id: KernelId,
        reason: KernelLifecycleEventReason,
        arg: KernelMutationArgs | None = None,
    ) -> None:
        now = datetime.now(tzutc())
        update_arg = arg or KernelMutationArgs(
            status=KernelStatus.TERMINATING,
            status_info=reason,
            status_data={
                "kernel": {"exit_code": None},
                "session": {"status": "terminating"},
            },
        )
        await KernelRow.set_status_by_kernel_id(db.sa_engine, (kernel_id,), update_arg, now)

    @staticmethod
    async def mark_terminated(
        db: DBContext,
        kernel_id: KernelId,
        reason: str | KernelLifecycleEventReason,
        arg: KernelMutationArgs | None = None,
    ) -> None:
        now = datetime.now(tzutc())
        kern_stat = await redis_helper.execute(
            db.redis_stat,
            lambda r: r.get(str(kernel_id)),
        )
        update_arg = arg or KernelMutationArgs(
            status=KernelStatus.TERMINATED,
            status_info=reason,
            last_stat=msgpack.unpackb(kern_stat),
        )
        await KernelRow.set_status_by_kernel_id(db.sa_engine, (kernel_id,), update_arg, now)

    @staticmethod
    async def handle_terminated(
        db: DBContext,
        kernel_id: KernelId,
        reason: str | KernelLifecycleEventReason,
        arg: KernelMutationArgs | None = None,
        exit_code: int | None = None,
    ) -> AgentId | None:
        kernel = await KernelRow.get_kernel_to_update_status(db.sa_engine, (kernel_id,))
        if kernel is None or kernel.status in (
            KernelStatus.CANCELLED,
            KernelStatus.TERMINATED,
            KernelStatus.RESTARTING,
        ):
            # Skip if non-existent, already terminated, or restarting.
            return None
        now = datetime.now(tzutc())
        kern_stat = await redis_helper.execute(
            db.redis_stat,
            lambda r: r.get(str(kernel_id)),
        )
        update_arg = arg or KernelMutationArgs(
            status=KernelStatus.TERMINATED,
            status_info=reason,
            status_data=sql_json_merge(
                KernelRow.status_data,
                ("kernel",),
                {"exit_code": exit_code},
            ),
            last_stat=msgpack.unpackb(kern_stat),
        )
        await KernelRow.set_status_by_kernel_id(db.sa_engine, (kernel_id,), update_arg, now)
        await recalc_concurrency_used(db, kernel.access_key)
        return kernel.agent

    @classmethod
    async def finalize_running(
        cls,
        db: DBContext,
        kernel_id: KernelId,
        update_arg: KernelMutationArgs,
    ) -> bool:
        from ..models.kernel import KernelRow

        update_arg.status = KernelStatus.RUNNING
        if not (await KernelRow.is_transitable(db.sa_engine, kernel_id, update_arg.status)):
            # TODO: log or raise error
            return False

        await KernelRow.set_status_by_kernel_id(db.sa_engine, (kernel_id,), update_arg)
        return True


async def recalc_concurrency_used(db: DBContext, access_key: AccessKey) -> None:
    concurrency_used, sftp_concurrency_used = await KernelRow.get_concurrency(
        db.sa_engine, access_key
    )
    await redis_helper.execute(
        db.redis_stat,
        lambda r: r.set(
            f"keypair.concurrency_used.{access_key}",
            concurrency_used,
        ),
    )
    await redis_helper.execute(
        db.redis_stat,
        lambda r: r.set(
            f"keypair.sftp_concurrency_used.{access_key}",
            sftp_concurrency_used,
        ),
    )
