"""Session and kernel lifecycle data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ArchName,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.data.network.types import NetworkType
from ai.backend.manager.data.session.types import SchedulingResult, SessionInfo
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import MainKernelNotFound, TooManyKernelsFound

from .image import ImageConfigData


@dataclass
class KernelBindingData:
    """Kernel-agent binding data for precondition checking and session starting."""

    kernel_id: KernelId
    agent_id: AgentId | None
    agent_addr: str | None
    resource_group: str
    image: str
    image_id: UUID | None
    architecture: ArchName
    status: KernelStatus | None = None
    status_changed: float | None = None
    cluster_role: str = DEFAULT_ROLE
    cluster_idx: int = 0
    local_rank: int = 0
    cluster_hostname: str | None = None
    uid: int | None = None
    main_gid: int | None = None
    gids: list[int] = field(default_factory=list)
    requested_slots: ResourceSlot = field(default_factory=ResourceSlot)
    resource_opts: dict[str, Any] = field(default_factory=dict)
    bootstrap_script: str | None = None
    startup_command: str | None = None
    preopen_ports: list[int] = field(default_factory=list)
    internal_data: dict[str, Any] | None = None
    vfolder_mounts: list[Any] = field(
        default_factory=list
    )  # Would be list[VFolderMount] in full impl


@dataclass
class SessionDataForPull:
    """Data for a session that needs image pulling."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    kernels: list[KernelBindingData]


@dataclass
class SessionDataForStart:
    """Data for a session ready to start with full details."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    session_type: SessionTypes
    name: str
    cluster_mode: ClusterMode
    kernels: list[KernelBindingData]
    user_uuid: UUID
    user_email: str
    user_name: str
    environ: dict[str, str]
    network_type: NetworkType | None = None
    network_id: str | None = None


@dataclass
class ScheduledSessionData:
    """Data for a scheduled session ready for precondition check."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    session_type: SessionTypes
    name: str
    kernels: list[KernelBindingData]
    # Additional fields for PREPARED sessions
    cluster_mode: ClusterMode | None = None
    user_uuid: UUID | None = None
    user_email: str | None = None
    user_name: str | None = None
    network_type: NetworkType | None = None
    network_id: str | None = None


@dataclass
class SessionsForPullWithImages:
    """Sessions for image pulling with their image configurations."""

    sessions: list[SessionDataForPull]
    image_configs: dict[UUID, ImageConfigData]


@dataclass
class SessionsForStartWithImages:
    """Sessions for starting with their image configurations."""

    sessions: list[SessionDataForStart]
    image_configs: dict[UUID, ImageConfigData]


@dataclass
class ScheduledSessionsWithImages:
    """Scheduled sessions with their image configurations."""

    sessions: list[ScheduledSessionData]
    image_configs: dict[UUID, ImageConfigData]


@dataclass
class KernelStartData:
    """Kernel data for starting a session."""

    kernel_id: UUID
    agent_id: AgentId
    agent_addr: str
    resource_group: str
    image: str
    image_id: UUID | None
    architecture: ArchName
    cluster_role: str
    cluster_idx: int
    requested_slots: ResourceSlot
    resource_opts: dict[str, Any]
    preopen_ports: list[int]
    container_id: str | None = None
    cluster_hostname: str | None = None
    bootstrap_script: str | None = None
    startup_command: str | None = None


@dataclass
class PreparedSessionData:
    """Data for a prepared session ready to start."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    session_type: SessionTypes
    name: str
    cluster_mode: ClusterMode
    kernels: list[KernelStartData]
    user_uuid: UUID
    user_email: str
    user_name: str
    network_type: NetworkType | None = None
    network_id: str | None = None


@dataclass
class PreparedSessionsWithImages:
    """Prepared sessions with their image configurations."""

    sessions: list[PreparedSessionData]
    image_configs: dict[UUID, ImageConfigData]


@dataclass(frozen=True)
class LastPhase:
    """The session's last scheduling-history record of the phase in progress.

    Absent when the session has no record of that phase yet. Read by the
    coordinator's failure classification: ``attempts`` against the retry
    budget, ``started_at`` against the timeout, and ``result`` to tell an
    attempt from a skip.

    Attributes:
        attempts: How many times the phase was recorded, skips included
        started_at: When the phase was first recorded
        result: What the record ended in
    """

    attempts: int
    started_at: datetime
    result: SchedulingResult


@dataclass
class SessionWithKernels:
    """
    Bundles a session with its associated kernels.

    This is the primary data unit for scheduler operations,
    representing a session and all its kernels as an atomic unit.

    Attributes:
        session_info: Session information including lifecycle data
        kernel_infos: List of kernels belonging to this session
        last_phase: The session's last record of the phase being processed,
                   or None when it has none yet
    """

    session_info: SessionInfo
    kernel_infos: list[KernelInfo]
    last_phase: LastPhase | None = None

    @property
    def main_kernel(self) -> KernelInfo:
        """Get the main kernel (kernel with DEFAULT_ROLE as cluster_role)."""
        main_kernels = [k for k in self.kernel_infos if k.cluster.cluster_role == DEFAULT_ROLE]
        if len(main_kernels) > 1:
            raise TooManyKernelsFound(
                f"Session {self.session_info.identity.id} has more than 1 main kernel"
            )
        if len(main_kernels) == 0:
            raise MainKernelNotFound(f"Session {self.session_info.identity.id} has no main kernel")
        return main_kernels[0]
