from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import datetime, tzinfo
from typing import (
    TYPE_CHECKING,
    Any,
)

import sqlalchemy as sa
import yarl
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import (
    Mapped,
    foreign,
    mapped_column,
    noload,
    relationship,
    selectinload,
)

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
    VFolderMount,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.kernel.types import (
    ClusterConfig,
    ImageInfo,
    KernelInfo,
    KernelStatus,
    LifecycleStatus,
    Metadata,
    Metrics,
    NetworkConfig,
    RelatedSessionInfo,
    ResourceInfo,
    RuntimeConfig,
    UserPermission,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.agent import AgentRow
    from ai.backend.manager.models.group import GroupRow
    from ai.backend.manager.models.image import ImageRow
    from ai.backend.manager.models.session import SessionRow
    from ai.backend.manager.models.user import UserRow

from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.base import (
    GUID,
    Base,
    KernelIDColumnType,
    ResourceSlotColumn,
    SessionIDColumnType,
    StrEnumType,
    StructuredJSONObjectListColumn,
    URLColumn,
)
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
)

__all__ = (
    "AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES",
    "DEAD_KERNEL_STATUSES",
    "LIVE_STATUS",
    "RESOURCE_USAGE_KERNEL_STATUSES",
    "USER_RESOURCE_OCCUPYING_KERNEL_STATUSES",
    "KernelRow",
    "kernels",
)

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models.kernel"))


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


def default_hostname(context: Any) -> str:
    params = context.get_current_parameters()
    return f"{params['cluster_role']}{params['cluster_idx']}"


# Defined for avoiding circular import
def _get_user_row_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.user import UserRow

    return UserRow.uuid == foreign(KernelRow.user_uuid)


class KernelRow(Base):  # type: ignore[misc]
    __tablename__ = "kernels"

    # The Backend.AI-side UUID for each kernel
    # (mapped to a container in the docker backend and a pod in the k8s backend)
    id: Mapped[KernelId] = mapped_column(
        "id", KernelIDColumnType, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    # session_id == id when the kernel is the main container in a multi-container session or a
    # single-container session.
    # Otherwise, it refers the kernel ID of the main container of the belonged multi-container session.
    session_id: Mapped[SessionId] = mapped_column(
        "session_id",
        SessionIDColumnType,
        sa.ForeignKey("sessions.id"),
        unique=False,
        index=True,
        nullable=False,
    )
    session_creation_id: Mapped[str | None] = mapped_column(
        "session_creation_id", sa.String(length=32), unique=False, index=False, nullable=True
    )
    session_name: Mapped[str | None] = mapped_column(
        "session_name", sa.String(length=128), unique=False, index=True, nullable=True
    )  # previously sess_id
    session_type: Mapped[SessionTypes] = mapped_column(
        "session_type",
        StrEnumType(SessionTypes, use_name=True),
        index=True,
        nullable=False,  # previously sess_type
        default=SessionTypes.INTERACTIVE,
        server_default=SessionTypes.INTERACTIVE.name,
    )
    cluster_mode: Mapped[str] = mapped_column(
        "cluster_mode",
        sa.String(length=16),
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE.name,
    )
    cluster_size: Mapped[int] = mapped_column("cluster_size", sa.Integer, nullable=False, default=1)
    cluster_role: Mapped[str] = mapped_column(
        "cluster_role", sa.String(length=16), nullable=False, default=DEFAULT_ROLE, index=True
    )
    cluster_idx: Mapped[int] = mapped_column("cluster_idx", sa.Integer, nullable=False, default=0)
    local_rank: Mapped[int] = mapped_column("local_rank", sa.Integer, nullable=False, default=0)
    cluster_hostname: Mapped[str] = mapped_column(
        "cluster_hostname", sa.String(length=64), nullable=False, default=default_hostname
    )
    uid: Mapped[int | None] = mapped_column(
        "uid", sa.Integer, nullable=True, server_default=sa.null()
    )
    main_gid: Mapped[int | None] = mapped_column(
        "main_gid", sa.Integer, nullable=True, server_default=sa.null()
    )
    gids: Mapped[list[int] | None] = mapped_column(
        "gids", sa.ARRAY(sa.Integer), nullable=True, server_default=sa.null()
    )

    # Resource ownership
    scaling_group: Mapped[str] = mapped_column(
        "scaling_group", sa.ForeignKey("scaling_groups.name"), index=True, nullable=False
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        sa.ForeignKey("scaling_groups.id"),
        index=True,
        nullable=False,
    )
    agent: Mapped[str | None] = mapped_column(
        "agent", sa.String(length=64), sa.ForeignKey("agents.id"), nullable=True
    )
    agent_addr: Mapped[str | None] = mapped_column(
        "agent_addr", sa.String(length=128), nullable=True
    )
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), sa.ForeignKey("domains.name"), nullable=False
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        "group_id", GUID, sa.ForeignKey("groups.id"), nullable=False
    )
    user_uuid: Mapped[uuid.UUID] = mapped_column("user_uuid", GUID, nullable=False)
    access_key: Mapped[str | None] = mapped_column(
        "access_key", sa.String(length=20), nullable=True
    )
    # `image` is a string representing canonical name which shaped "<REGISTRY>/<PROJECT>/<IMAGE_NAME>:<TAG>".
    # Kept as historical audit data; active reference is `image_id`.
    image: Mapped[str | None] = mapped_column("image", sa.String(length=512), nullable=True)
    image_id: Mapped[ImageID | None] = mapped_column(
        "image_id",
        GUID(ImageID),
        sa.ForeignKey("images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    architecture: Mapped[str | None] = mapped_column(
        "architecture", sa.String(length=32), default="x86_64", nullable=True
    )
    registry: Mapped[str | None] = mapped_column("registry", sa.String(length=512), nullable=True)
    tag: Mapped[str | None] = mapped_column("tag", sa.String(length=64), nullable=True)
    # Resource occupation
    container_id: Mapped[str | None] = mapped_column(
        "container_id", sa.String(length=64), nullable=True
    )
    # DEPRECATED (Phase 3, BA-4308): No longer the source of truth.
    # Kernel resource allocations are now tracked by the normalized
    # resource_allocations table.  Retained for historical audit.
    occupied_slots: Mapped[ResourceSlot] = mapped_column(
        "occupied_slots", ResourceSlotColumn(), nullable=False
    )
    # DEPRECATED (Phase 3, BA-4308): See resource_allocations table.
    requested_slots: Mapped[ResourceSlot] = mapped_column(
        "requested_slots", ResourceSlotColumn(), nullable=False
    )
    occupied_shares: Mapped[dict[str, Any]] = mapped_column(
        "occupied_shares", pgsql.JSONB(), nullable=False, default={}
    )  # legacy
    environ: Mapped[list[str] | None] = mapped_column("environ", sa.ARRAY(sa.String), nullable=True)
    mounts: Mapped[list[str] | None] = mapped_column(
        "mounts", sa.ARRAY(sa.String), nullable=True
    )  # list of list; legacy since 22.03
    mount_map: Mapped[dict[str, Any] | None] = mapped_column(
        "mount_map", pgsql.JSONB(), nullable=True, default={}
    )  # legacy since 22.03
    vfolder_mounts: Mapped[list[VFolderMount] | None] = mapped_column(
        "vfolder_mounts", StructuredJSONObjectListColumn(VFolderMount), nullable=True
    )
    attached_devices: Mapped[dict[str, Any] | None] = mapped_column(
        "attached_devices", pgsql.JSONB(), nullable=True, default={}
    )
    resource_opts: Mapped[dict[str, Any] | None] = mapped_column(
        "resource_opts", pgsql.JSONB(), nullable=True, default={}
    )
    bootstrap_script: Mapped[str | None] = mapped_column(
        "bootstrap_script", sa.String(length=16 * 1024), nullable=True
    )
    # Port mappings
    # If kernel_host is NULL, it is assumed to be same to the agent host or IP.
    kernel_host: Mapped[str | None] = mapped_column(
        "kernel_host", sa.String(length=128), nullable=True
    )
    repl_in_port: Mapped[int] = mapped_column("repl_in_port", sa.Integer(), nullable=False)
    repl_out_port: Mapped[int] = mapped_column("repl_out_port", sa.Integer(), nullable=False)
    stdin_port: Mapped[int] = mapped_column(
        "stdin_port", sa.Integer(), nullable=False
    )  # legacy for stream_pty
    stdout_port: Mapped[int] = mapped_column(
        "stdout_port", sa.Integer(), nullable=False
    )  # legacy for stream_pty
    service_ports: Mapped[list[dict[str, Any]] | None] = mapped_column(
        "service_ports", pgsql.JSONB(), nullable=True
    )
    preopen_ports: Mapped[list[int] | None] = mapped_column(
        "preopen_ports", sa.ARRAY(sa.Integer), nullable=True
    )
    use_host_network: Mapped[bool] = mapped_column(
        "use_host_network", sa.Boolean(), default=False, nullable=False
    )
    # Lifecycle
    created_at: Mapped[datetime | None] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        index=True,
        nullable=True,
    )
    terminated_at: Mapped[datetime | None] = mapped_column(
        "terminated_at", sa.DateTime(timezone=True), nullable=True, default=sa.null(), index=True
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        "starts_at", sa.DateTime(timezone=True), nullable=True, default=sa.null()
    )
    status: Mapped[KernelStatus] = mapped_column(
        "status",
        StrEnumType(KernelStatus),
        default=KernelStatus.PENDING,
        server_default=KernelStatus.PENDING.name,
        nullable=False,
        index=True,
    )
    status_changed: Mapped[datetime | None] = mapped_column(
        "status_changed", sa.DateTime(timezone=True), nullable=True, index=True
    )
    status_info: Mapped[str | None] = mapped_column(
        "status_info", sa.Unicode(), nullable=True, default=sa.null()
    )
    # status_info contains a kebab-cased string that expresses a summary of the last status change.
    # Examples: "user-requested", "self-terminated", "predicate-checks-failed", "no-available-instances"
    status_data: Mapped[dict[str, Any] | None] = mapped_column(
        "status_data", pgsql.JSONB(), nullable=True, default=sa.null()
    )
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
    #           // see the sokovan scheduler validator modules for possible messages
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
    status_history: Mapped[dict[str, Any] | None] = mapped_column(
        "status_history", pgsql.JSONB(), nullable=True, default=sa.null()
    )
    callback_url: Mapped[yarl.URL | None] = mapped_column(
        "callback_url", URLColumn, nullable=True, default=sa.null()
    )
    startup_command: Mapped[str | None] = mapped_column("startup_command", sa.Text, nullable=True)
    result: Mapped[SessionResult] = mapped_column(
        "result",
        StrEnumType(SessionResult, use_name=True),
        default=SessionResult.UNDEFINED,
        server_default=SessionResult.UNDEFINED.name,
        nullable=False,
        index=True,
    )
    internal_data: Mapped[dict[str, Any] | None] = mapped_column(
        "internal_data", pgsql.JSONB(), nullable=True
    )
    container_log: Mapped[bytes | None] = mapped_column(
        "container_log", sa.LargeBinary(), nullable=True
    )
    # Resource metrics measured upon termination
    num_queries: Mapped[int | None] = mapped_column(
        "num_queries", sa.BigInteger(), default=0, nullable=True
    )
    last_stat: Mapped[dict[str, Any] | None] = mapped_column(
        "last_stat", pgsql.JSONB(), nullable=True, default=sa.null()
    )
    last_seen: Mapped[datetime | None] = mapped_column(
        "last_seen",
        sa.DateTime(timezone=True),
        nullable=True,
        default=sa.null(),
        server_default=sa.null(),
    )
    last_observed_at: Mapped[datetime | None] = mapped_column(
        "last_observed_at",
        sa.DateTime(timezone=True),
        nullable=True,
        default=sa.null(),
        server_default=sa.null(),
    )

    __table_args__ = (
        # indexing
        sa.Index("ix_kernels_sess_id_role", "session_id", "cluster_role", unique=False),
        sa.Index("ix_kernels_status_role", "status", "cluster_role"),
        sa.Index(
            "ix_kernels_updated_order",
            sa.func.greatest("created_at", "terminated_at", "status_changed"),
            unique=False,
        ),
        # Partial index for running kernels (fair share observation)
        sa.Index(
            "ix_kernels_fair_share_running",
            "scaling_group",
            postgresql_where=sa.text("terminated_at IS NULL AND starts_at IS NOT NULL"),
        ),
        # Partial index for terminated kernels (fair share observation)
        sa.Index(
            "ix_kernels_fair_share_terminated",
            "scaling_group",
            "terminated_at",
            postgresql_where=sa.text("terminated_at IS NOT NULL AND starts_at IS NOT NULL"),
        ),
    )

    session: Mapped[SessionRow] = relationship("SessionRow", back_populates="kernels")
    image_row: Mapped[ImageRow | None] = relationship(
        "ImageRow",
        foreign_keys="KernelRow.image_id",
    )
    agent_row: Mapped[AgentRow | None] = relationship("AgentRow", back_populates="kernels")
    group_row: Mapped[GroupRow] = relationship("GroupRow", back_populates="kernels")
    user_row: Mapped[UserRow] = relationship(
        "UserRow",
        primaryjoin=_get_user_row_join_condition,
        back_populates="kernels",
        foreign_keys="KernelRow.user_uuid",
    )

    @property
    def used_time(self) -> str | None:
        if self.terminated_at is not None and self.created_at is not None:
            return str(self.terminated_at - self.created_at)
        return None

    def get_used_days(self, local_tz: tzinfo) -> int | None:
        if self.terminated_at is not None and self.created_at is not None:
            return (
                self.terminated_at.astimezone(local_tz).toordinal()
                - self.created_at.astimezone(local_tz).toordinal()
                + 1
            )
        return None

    @staticmethod
    async def batch_load_main_kernels_by_session_id(
        session: SASession, session_ids: list[uuid.UUID]
    ) -> Sequence[KernelRow]:
        query = (
            sa.select(KernelRow)
            .where(KernelRow.session_id.in_(session_ids))
            .where(KernelRow.cluster_role == DEFAULT_ROLE)
        )
        return (await session.execute(query)).scalars().all()

    @staticmethod
    async def get_kernel(
        db: ExtendedAsyncSAEngine, kern_id: uuid.UUID, allow_stale: bool = False
    ) -> KernelRow:
        from ai.backend.manager.models.agent import AgentStatus

        async def _query() -> KernelRow:
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
                        and (k.agent_row is not None and k.agent_row.status == AgentStatus.ALIVE)
                    ]
                if not cand:
                    raise SessionNotFound
                return cand[0]

        return await execute_with_retry(_query)

    def delegate_ownership(self, user_uuid: uuid.UUID, access_key: AccessKey) -> None:
        self.user_uuid = user_uuid
        self.access_key = access_key

    def to_kernel_info(self) -> KernelInfo:
        return KernelInfo(
            id=self.id,
            session=RelatedSessionInfo(
                session_id=str(self.session_id),
                creation_id=self.session_creation_id,
                name=self.session_name,
                session_type=self.session_type,
            ),
            user_permission=UserPermission(
                user_uuid=self.user_uuid,
                access_key=self.access_key or "",
                domain_name=self.domain_name,
                group_id=self.group_id,
                uid=self.uid,
                main_gid=self.main_gid,
                gids=self.gids,
            ),
            image=ImageInfo(
                image_id=self.image_id,
                identifier=ImageIdentifier(
                    canonical=self.image,
                    architecture=self.architecture or "",
                )
                if self.image
                else None,
                registry=self.registry,
                tag=self.tag,
                architecture=self.architecture,
            ),
            network=NetworkConfig(
                kernel_host=self.kernel_host,
                repl_in_port=self.repl_in_port,
                repl_out_port=self.repl_out_port,
                stdin_port=self.stdin_port,
                stdout_port=self.stdout_port,
                service_ports=self.service_ports,
                preopen_ports=self.preopen_ports,
                use_host_network=self.use_host_network,
            ),
            cluster=ClusterConfig(
                cluster_mode=self.cluster_mode,
                cluster_size=self.cluster_size,
                cluster_role=self.cluster_role,
                cluster_idx=self.cluster_idx,
                local_rank=self.local_rank,
                cluster_hostname=self.cluster_hostname,
            ),
            resource=ResourceInfo(
                scaling_group=self.scaling_group,
                resource_group_id=self.resource_group_id,
                agent=self.agent,
                agent_addr=self.agent_addr,
                container_id=self.container_id,
                occupied_slots=self.occupied_slots,
                requested_slots=self.requested_slots,
                occupied_shares=self.occupied_shares,
                attached_devices=self.attached_devices or {},
                resource_opts=self.resource_opts or {},
            ),
            runtime=RuntimeConfig(
                environ=self.environ,
                mounts=self.mounts,
                mount_map=self.mount_map,
                vfolder_mounts=[m.to_json() for m in self.vfolder_mounts]
                if self.vfolder_mounts
                else None,
                bootstrap_script=self.bootstrap_script,
                startup_command=self.startup_command,
            ),
            lifecycle=LifecycleStatus(
                status=self.status,
                result=self.result,
                created_at=self.created_at,
                terminated_at=self.terminated_at,
                starts_at=self.starts_at,
                status_changed=self.status_changed,
                status_info=self.status_info,
                status_data=self.status_data,
                status_history=self.status_history,
                last_seen=self.last_seen,
                last_observed_at=self.last_observed_at,
            ),
            metrics=Metrics(
                num_queries=self.num_queries or 0,
                last_stat=self.last_stat,
                container_log=self.container_log,
            ),
            metadata=Metadata(
                callback_url=str(self.callback_url) if self.callback_url else None,
                internal_data=self.internal_data,
            ),
        )


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
