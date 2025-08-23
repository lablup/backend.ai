"""Types for session creation and enqueueing."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, Union
from uuid import UUID

import yarl

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelEnqueueingConfig,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
    VFolderMount,
)
from ai.backend.manager.models import NetworkRow
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.types import UserScope


@dataclass
class SessionCreationSpec:
    """Specification for creating a new session."""

    # Required parameters
    session_creation_id: str
    session_name: str
    access_key: AccessKey
    user_scope: UserScope
    session_type: SessionTypes
    cluster_mode: ClusterMode
    cluster_size: int
    priority: int
    resource_policy: dict
    kernel_specs: list[KernelEnqueueingConfig]
    creation_spec: dict

    # Optional parameters
    scaling_group: Optional[str] = None
    session_tag: Optional[str] = None
    starts_at: Optional[datetime] = None
    batch_timeout: Optional[timedelta] = None
    dependency_sessions: Optional[list[SessionId]] = None
    callback_url: Optional[yarl.URL] = None
    route_id: Optional[UUID] = None
    sudo_session_enabled: bool = False
    network: Optional[NetworkRow] = None
    agent_list: Optional[list[str]] = None
    internal_data: Optional[dict] = None
    public_sgroup_only: bool = True


@dataclass
class KernelEnqueueData:
    """Data for each kernel in the session."""

    id: KernelId
    session_id: SessionId
    session_creation_id: str
    session_name: str
    session_type: SessionTypes
    cluster_mode: str  # Store as string for DB
    cluster_size: int
    cluster_role: str
    cluster_idx: int
    local_rank: int
    cluster_hostname: str
    agent: Optional[str]  # AgentId if pre-assigned
    scaling_group: str
    domain_name: str
    group_id: UUID
    user_uuid: UUID
    access_key: AccessKey
    image: str  # Canonical image name
    architecture: str
    registry: str
    tag: Optional[str]
    starts_at: Optional[datetime]
    status: str  # KernelStatus.PENDING
    status_history: dict[str, str]
    occupied_slots: ResourceSlot
    requested_slots: ResourceSlot
    occupied_shares: dict
    resource_opts: dict
    environ: list[str]  # List of "KEY=VALUE" strings
    bootstrap_script: Optional[str]
    startup_command: Optional[str]
    internal_data: dict[str, Any]
    callback_url: Optional[yarl.URL]
    mounts: list[str]  # Legacy field for compatibility
    vfolder_mounts: list[VFolderMount]
    preopen_ports: list[int]
    use_host_network: bool

    # Port fields (initially 0)
    repl_in_port: int = 0
    repl_out_port: int = 0
    stdin_port: int = 0
    stdout_port: int = 0

    # Container user info
    uid: int = field(default=1000)
    main_gid: int = field(default=1000)
    gids: list[int] = field(default_factory=list)


@dataclass
class SessionEnqueueData:
    """Prepared data ready to be enqueued in database."""

    # Associated data
    kernels: list[KernelEnqueueData]
    dependencies: list[SessionId]

    id: SessionId
    creation_id: str
    name: str
    access_key: AccessKey
    user_uuid: UUID
    group_id: UUID
    domain_name: str
    scaling_group_name: str
    session_type: SessionTypes
    cluster_mode: str  # Store as string for DB
    cluster_size: int
    priority: int
    status: str  # SessionStatus.PENDING
    status_history: dict[str, str]
    requested_slots: ResourceSlot
    occupying_slots: ResourceSlot
    vfolder_mounts: list[VFolderMount]
    environ: dict[str, str]
    tag: Optional[str]
    starts_at: Optional[datetime]
    batch_timeout: Optional[int]  # seconds
    callback_url: Optional[yarl.URL]
    images: list[str]
    network_type: Optional[NetworkType] = None
    network_id: Optional[str] = None
    bootstrap_script: Optional[str] = None
    use_host_network: bool = False
    timeout: Optional[int] = None


@dataclass
class SessionDependencyData:
    """Data for session dependency relationships."""

    session_id: SessionId
    depends_on: SessionId


@dataclass
class ScalingGroupNetworkInfo:
    """Network configuration from scaling group."""

    use_host_network: bool
    wsproxy_addr: Optional[str] = None


@dataclass
class ImageInfo:
    """Resolved image information."""

    canonical: str
    architecture: str
    registry: str
    labels: dict[str, Any]
    # Resource spec maps slot names to {"min": value, "max": value}
    # Values can be strings (for BinarySize), numbers, or None
    resource_spec: dict[str, dict[str, Union[str, int, Decimal, None]]]


@dataclass
class AllowedScalingGroup:
    """Allowed scaling group for a user."""

    name: str
    is_private: bool


@dataclass
class UserContainerInfo:
    """User container UID/GID information."""

    uid: int
    main_gid: int
    supplementary_gids: list[int]


@dataclass
class SessionCreationContext:
    """All data needed for session creation, fetched in a single batch."""

    # Scaling group network info
    scaling_group_network: ScalingGroupNetworkInfo

    # Allowed scaling groups for validation
    allowed_scaling_groups: list[AllowedScalingGroup]

    # Image information for all kernels
    image_infos: dict[str, ImageInfo]  # keyed by image reference

    # Vfolder mounts
    vfolder_mounts: list[VFolderMount]

    # Dotfile data
    dotfile_data: dict[str, Any]

    # User container info
    user_container_info: Optional[UserContainerInfo] = None
