from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any, Optional
from uuid import UUID

from ai.backend.common.data.vfolder.types import VFolderMountData
from ai.backend.common.types import (
    AccessKey,
    CIStrEnum,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.network import NetworkType


class SessionStatus(CIStrEnum):
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

    @classmethod
    def kernel_awaiting_statuses(cls) -> set["SessionStatus"]:
        return {
            cls.PREPARING,
            cls.PULLING,
            cls.CREATING,
            cls.TERMINATING,
        }

    @classmethod
    @lru_cache(maxsize=1)
    def resource_occupied_statuses(cls) -> frozenset["SessionStatus"]:
        return frozenset(
            status
            for status in cls
            if status
            not in (
                cls.PENDING,
                cls.TERMINATED,
                cls.CANCELLED,
            )
        )

    @classmethod
    @lru_cache(maxsize=1)
    def terminatable_statuses(cls) -> frozenset["SessionStatus"]:
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
    def terminal_statuses(cls) -> frozenset["SessionStatus"]:
        return frozenset((
            cls.ERROR,
            cls.TERMINATED,
            cls.CANCELLED,
        ))

    @classmethod
    @lru_cache(maxsize=1)
    def retriable_statuses(cls) -> frozenset["SessionStatus"]:
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

    def is_terminal(self) -> bool:
        return self in self.terminal_statuses()


# TODO: Add proper types
@dataclass
class SessionData:
    id: UUID
    session_type: SessionTypes
    priority: int
    cluster_mode: ClusterMode
    cluster_size: int
    domain_name: str
    group_id: UUID
    user_uuid: UUID
    occupying_slots: Any  # TODO: ResourceSlot?
    requested_slots: Any
    use_host_network: bool
    created_at: datetime = field(compare=False)
    status: "SessionStatus"
    result: SessionResult
    num_queries: int
    creation_id: Optional[str]
    name: Optional[str]
    access_key: Optional[AccessKey]
    agent_ids: Optional[list[str]]
    images: Optional[list[str]]
    tag: Optional[str]
    vfolder_mounts: Optional[list[VFolderMountData]]
    environ: Optional[dict[str, Any]]
    bootstrap_script: Optional[str]
    target_sgroup_names: Optional[list[str]]
    timeout: Optional[int]
    batch_timeout: Optional[int]
    terminated_at: Optional[datetime] = field(compare=False)
    scaling_group_name: Optional[str]
    starts_at: Optional[datetime] = field(compare=False)
    status_info: Optional[str] = field(compare=False)
    status_data: Optional[dict[str, Any]] = field(compare=False)
    status_history: Optional[dict[str, Any]] = field(compare=False)
    callback_url: Optional[str]
    startup_command: Optional[str]
    last_stat: Optional[dict[str, Any]] = field(compare=False)
    network_type: Optional[NetworkType]
    network_id: Optional[str]
    owner: Optional[UserData] = field(compare=False)

    # Loaded from relationship
    service_ports: Optional[str]


@dataclass
class SessionIdentity:
    id: SessionId
    creation_id: str
    name: str
    session_type: SessionTypes
    priority: int


@dataclass
class SessionMetadata:
    name: str
    domain_name: str
    group_id: UUID
    user_uuid: UUID
    access_key: str
    session_type: SessionTypes
    priority: int
    created_at: Optional[datetime]
    tag: Optional[str]


@dataclass
class ResourceSpec:
    cluster_mode: str
    cluster_size: int
    occupying_slots: ResourceSlot
    requested_slots: ResourceSlot
    scaling_group_name: Optional[str]
    target_sgroup_names: Optional[list[str]]
    agent_ids: Optional[list[str]]


@dataclass
class ImageSpec:
    images: Optional[list[str]]
    tag: Optional[str]


@dataclass
class MountSpec:
    vfolder_mounts: Optional[list[dict[str, Any]]]


@dataclass
class SessionExecution:
    environ: Optional[dict[str, Any]]
    bootstrap_script: Optional[str]
    startup_command: Optional[str]
    use_host_network: bool
    callback_url: Optional[str]


@dataclass
class SessionLifecycle:
    status: SessionStatus
    result: SessionResult
    created_at: Optional[datetime]
    terminated_at: Optional[datetime]
    starts_at: Optional[datetime]
    status_changed: Optional[datetime]
    batch_timeout: Optional[int]
    status_info: Optional[str]
    status_data: Optional[Mapping[str, Any]]
    status_history: Optional[dict[str, Any]]


@dataclass
class SessionMetrics:
    num_queries: int
    last_stat: Optional[dict[str, Any]]


@dataclass
class SessionNetwork:
    network_type: Optional[NetworkType]
    network_id: Optional[str]


@dataclass
class SessionInfo:
    identity: SessionIdentity
    metadata: SessionMetadata
    resource: ResourceSpec
    image: ImageSpec
    mounts: MountSpec
    execution: SessionExecution
    lifecycle: SessionLifecycle
    metrics: SessionMetrics
    network: SessionNetwork
