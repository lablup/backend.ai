from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Optional, override
from uuid import UUID

from pydantic import BaseModel

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
from ai.backend.manager.types import Creator

if TYPE_CHECKING:
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


# ========== Scheduling History Types ==========


class SchedulingResult(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"


class SubStepResult(BaseModel):
    """Sub-step result for scheduling history."""

    step: str
    result: SchedulingResult
    error_code: Optional[str] = None
    message: Optional[str] = None


@dataclass
class SessionSchedulingHistoryData:
    """Domain model for session scheduling history."""

    id: UUID
    session_id: SessionId

    phase: str  # ScheduleType value
    from_status: Optional[SessionStatus]
    to_status: Optional[SessionStatus]

    result: SchedulingResult
    error_code: Optional[str]
    message: str

    sub_steps: Optional[list[SubStepResult]]

    attempts: int
    created_at: datetime
    updated_at: datetime


@dataclass
class SessionSchedulingHistoryCreator(Creator):
    """Creator for session scheduling history."""

    session_id: SessionId
    phase: str  # ScheduleType value
    result: SchedulingResult
    message: str
    from_status: Optional[SessionStatus] = None
    to_status: Optional[SessionStatus] = None
    error_code: Optional[str] = None
    sub_steps: Optional[list[SubStepResult]] = None

    @override
    def fields_to_store(self) -> dict[str, Any]:
        sub_steps_json: list[dict[str, Any]] | None = None
        if self.sub_steps:
            sub_steps_json = [s.model_dump(mode="json") for s in self.sub_steps]
        return {
            "session_id": self.session_id,
            "phase": self.phase,
            "from_status": str(self.from_status) if self.from_status else None,
            "to_status": str(self.to_status) if self.to_status else None,
            "result": str(self.result),
            "error_code": self.error_code,
            "message": self.message,
            "sub_steps": sub_steps_json,
            "attempts": 1,
        }


@dataclass
class SessionSchedulingHistoryListResult:
    """Search result with pagination for session scheduling history."""

    items: list[SessionSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
