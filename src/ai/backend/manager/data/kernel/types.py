from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from ai.backend.common.types import (
    CIStrEnum,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.image.types import ImageIdentifier

if TYPE_CHECKING:
    from ai.backend.manager.data.session.types import SchedulingResult


class KernelStatus(CIStrEnum):
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

    @classmethod
    def having_containers(cls) -> set["KernelStatus"]:
        return {
            cls.PULLING,
            cls.CREATING,
            cls.RUNNING,
        }

    def have_container(self) -> bool:
        """
        Check if the current status is one of the statuses that have containers.
        """
        return self in KernelStatus.having_containers()

    @classmethod
    @lru_cache(maxsize=1)
    def resource_occupied_statuses(cls) -> frozenset["KernelStatus"]:
        """
        Returns a set of kernel statuses that are considered as resource-occupying.
        """
        return frozenset((
            cls.RUNNING,
            cls.TERMINATING,
        ))

    @classmethod
    @lru_cache(maxsize=1)
    def resource_requested_statuses(cls) -> frozenset["KernelStatus"]:
        """
        Returns a set of kernel statuses that are considered as resource-occupying.
        """
        return frozenset((
            cls.SCHEDULED,
            cls.PREPARING,
            cls.PULLING,
            cls.PREPARED,
            cls.CREATING,
        ))

    @classmethod
    @lru_cache(maxsize=1)
    def terminatable_statuses(cls) -> frozenset["KernelStatus"]:
        """Return statuses that can transition to TERMINATING."""
        return frozenset(
            status
            for status in cls
            if status
            not in (
                cls.PENDING,
                cls.TERMINATING,
                cls.TERMINATED,
                cls.CANCELLED,
                cls.ERROR,
            )
        )

    @classmethod
    @lru_cache(maxsize=1)
    def terminal_statuses(cls) -> frozenset["KernelStatus"]:
        """
        Returns a set of kernel statuses that are considered terminal.
        """
        return frozenset((
            cls.ERROR,
            cls.TERMINATED,
            cls.CANCELLED,
        ))

    @classmethod
    @lru_cache(maxsize=1)
    def retriable_statuses(cls) -> frozenset["KernelStatus"]:
        """
        Returns a set of kernel statuses that are considered retriable.
        """
        return frozenset(
            (
                status
                for status in cls
                if status
                not in (
                    cls.RUNNING,
                    cls.TERMINATING,
                    cls.TERMINATED,
                    cls.CANCELLED,
                )
            )
        )


@dataclass
class RelatedSessionInfo:
    session_id: str  # Session UUID
    creation_id: Optional[str]
    name: Optional[str]
    session_type: SessionTypes


@dataclass
class ClusterConfig:
    cluster_mode: str
    cluster_size: int
    cluster_role: str
    cluster_idx: int
    local_rank: int
    cluster_hostname: str


@dataclass
class UserPermission:
    user_uuid: UUID
    access_key: str
    domain_name: str
    group_id: UUID
    uid: Optional[int]
    main_gid: Optional[int]
    gids: Optional[list[int]]


@dataclass
class ResourceInfo:
    scaling_group: Optional[str]
    agent: Optional[str]
    agent_addr: Optional[str]
    container_id: Optional[str]
    occupied_slots: ResourceSlot
    requested_slots: ResourceSlot
    occupied_shares: dict[str, Any]
    attached_devices: dict[str, Any]
    resource_opts: dict[str, Any]


@dataclass
class ImageInfo:
    identifier: Optional[ImageIdentifier]
    registry: Optional[str]
    tag: Optional[str]
    architecture: Optional[str]


@dataclass
class RuntimeConfig:
    environ: Optional[list[str]]
    mounts: Optional[list[str]]  # legacy
    mount_map: Optional[dict[str, Any]]  # legacy
    vfolder_mounts: Optional[list[dict[str, Any]]]
    bootstrap_script: Optional[str]
    startup_command: Optional[str]


@dataclass
class NetworkConfig:
    kernel_host: Optional[str]
    repl_in_port: int
    repl_out_port: int
    stdin_port: int  # legacy
    stdout_port: int  # legacy
    service_ports: Optional[dict[str, Any]]
    preopen_ports: Optional[list[int]]
    use_host_network: bool


@dataclass
class LifecycleStatus:
    status: KernelStatus
    result: SessionResult
    created_at: Optional[datetime]
    terminated_at: Optional[datetime]
    starts_at: Optional[datetime]
    status_changed: Optional[datetime]
    status_info: Optional[str]
    status_data: Optional[Mapping[str, Any]]
    status_history: Optional[dict[str, Any]]
    last_seen: Optional[datetime]


@dataclass
class Metrics:
    num_queries: int
    last_stat: Optional[dict[str, Any]]
    container_log: Optional[bytes]


@dataclass
class Metadata:
    callback_url: Optional[str]
    internal_data: Optional[dict[str, Any]]


@dataclass
class KernelInfo:
    id: UUID  # Kernel UUID
    session: RelatedSessionInfo
    user_permission: UserPermission
    image: ImageInfo
    network: NetworkConfig
    cluster: ClusterConfig
    resource: ResourceInfo
    runtime: RuntimeConfig
    lifecycle: LifecycleStatus
    metrics: Metrics
    metadata: Metadata


# ========== Scheduling History Types ==========


class KernelSchedulingPhase(StrEnum):
    PREPARING = "PREPARING"
    PULLING = "PULLING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


@dataclass
class KernelSchedulingHistoryData:
    """Domain model for kernel scheduling history."""

    id: UUID
    kernel_id: KernelId
    session_id: SessionId

    phase: str  # ScheduleType value
    from_status: Optional[KernelSchedulingPhase]
    to_status: Optional[KernelSchedulingPhase]

    result: SchedulingResult
    error_code: Optional[str]
    message: str

    attempts: int
    created_at: datetime
    updated_at: datetime


@dataclass
class KernelSchedulingHistoryListResult:
    """Search result with pagination for kernel scheduling history."""

    items: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
