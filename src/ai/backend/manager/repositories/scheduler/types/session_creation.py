"""Types for session creation and enqueueing."""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, Self
from uuid import UUID

import yarl

from ai.backend.common.defs.session import SESSION_PRIORITY_DEFAULT
from ai.backend.common.docker import ImageRef
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
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.models import NetworkRow
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.types import UserScope


@dataclass
class UserContext:
    """User information for session creation."""

    uuid: UUID
    access_key: AccessKey
    role: str  # UserRole as string
    sudo_session_enabled: bool


@dataclass
class ContainerUserContext:
    """Container user UID/GID information."""

    uid: Optional[int]
    main_gid: Optional[int]
    supplementary_gids: list[int]


@dataclass
class ImageContext:
    """Resolved image information."""

    ref: ImageRef  # Image reference object
    labels: dict[str, Any]


@dataclass
class DeploymentContext:
    """Context data needed to create a session from deployment info."""

    created_user: UserContext
    session_owner: UserContext
    container_user: ContainerUserContext
    group_id: UUID
    resource_policy: dict[str, Any]
    image: ImageContext


@dataclass
class SessionUserInfo:
    user_scope: UserScope
    access_key: AccessKey
    resource_policy: dict[str, Any]  # Raw policy data


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
    designated_agent_list: Optional[list[str]] = None
    internal_data: Optional[dict] = None
    public_sgroup_only: bool = True

    @classmethod
    def from_deployment_info(
        cls, deployment_info: DeploymentInfo, context: DeploymentContext, route_id: UUID
    ) -> Self:
        session_creation_id = secrets.token_urlsafe(16)
        target_revision = deployment_info.target_revision()
        if target_revision is None:
            raise ValueError("Deployment has no target revision for session creation")

        # Prepare mount spec
        mount_spec = target_revision.mounts.to_mount_spec()

        # Prepare environment variables
        environ = target_revision.execution.environ or {}
        if "BACKEND_MODEL_NAME" not in environ:
            # Add model name to environment if not already present
            environ["BACKEND_MODEL_NAME"] = deployment_info.metadata.name

        # Create kernel specs for cluster
        DEFAULT_ROLE = "main"
        kernel_specs = []
        for idx in range(target_revision.resource_spec.cluster_size):
            kernel_spec = KernelEnqueueingConfig(
                image_ref=context.image.ref,
                cluster_role=DEFAULT_ROLE if idx == 0 else "worker",
                cluster_idx=idx + 1,
                local_rank=idx,
                cluster_hostname=f"{DEFAULT_ROLE}{idx + 1}" if idx == 0 else f"worker{idx}",
                creation_config={
                    "mounts": mount_spec.mounts,
                    "mount_map": mount_spec.mount_map,
                    "mount_options": mount_spec.mount_options,
                    "environ": environ,
                    "resources": target_revision.resource_spec.resource_slots,
                    "resource_opts": target_revision.resource_spec.resource_opts,
                },
                uid=context.container_user.uid,
                main_gid=context.container_user.main_gid,
                supplementary_gids=context.container_user.supplementary_gids,
                bootstrap_script=target_revision.execution.bootstrap_script or "",
                startup_command=target_revision.execution.startup_command,
            )
            kernel_specs.append(kernel_spec)

        return cls(
            session_creation_id=session_creation_id,
            session_name=f"{deployment_info.metadata.name}-{str(route_id)}",
            access_key=context.session_owner.access_key,
            user_scope=UserScope(
                domain_name=deployment_info.metadata.domain,
                group_id=context.group_id,
                user_uuid=context.session_owner.uuid,
                user_role=context.session_owner.role,
            ),
            session_type=SessionTypes.INFERENCE,
            cluster_mode=target_revision.resource_spec.cluster_mode,
            cluster_size=target_revision.resource_spec.cluster_size,
            priority=SESSION_PRIORITY_DEFAULT,
            resource_policy=context.resource_policy,
            kernel_specs=kernel_specs,
            creation_spec={
                "mounts": mount_spec.mounts,
                "mount_map": mount_spec.mount_map,
                "mount_options": mount_spec.mount_options,
                "model_definition_path": target_revision.mounts.model_definition_path,
                "runtime_variant": target_revision.execution.runtime_variant,
                "environ": environ,
                "scaling_group": deployment_info.metadata.resource_group,
                "resources": target_revision.resource_spec.resource_slots,
                "resource_opts": target_revision.resource_spec.resource_opts,
                "preopen_ports": None,
                "agent_list": None,
            },
            scaling_group=deployment_info.metadata.resource_group,
            session_tag=deployment_info.metadata.tag,
            callback_url=target_revision.execution.callback_url,
            route_id=route_id,
            sudo_session_enabled=context.session_owner.sudo_session_enabled,
        )


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
    uid: Optional[int] = field(default=None)
    main_gid: Optional[int] = field(default=None)
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
    designated_agent_list: Optional[list[str]]
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
    resource_spec: dict[str, dict[str, Optional[str | int | Decimal]]]


@dataclass
class AllowedScalingGroup:
    """Allowed scaling group for a user."""

    name: str
    is_private: bool
    scheduler_opts: ScalingGroupOpts


@dataclass
class ContainerUserInfo:
    """User container UID/GID information."""

    uid: Optional[int] = None
    main_gid: Optional[int] = None
    supplementary_gids: list[int] = field(default_factory=list)


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

    # User (UID/GID) inside container
    container_user_info: ContainerUserInfo
