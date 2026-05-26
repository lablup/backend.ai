"""Types for session creation and enqueueing."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID

from ai.backend.common.docker import ImageRef
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import (
    AccessKey,
    SessionId,
    SlotName,
    SlotTypes,
    VFolderMount,
)
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.models.scaling_group import ScalingGroupOpts


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

    uid: int | None
    main_gid: int | None
    supplementary_gids: list[int]


@dataclass
class ImageContext:
    """Resolved image information."""

    ref: ImageRef  # Image reference object
    labels: dict[str, Any]


@dataclass
class ResolvedPresetValues:
    """Resolved preset values ready for session injection."""

    environ: dict[str, str]
    args: list[str]


@dataclass
class DeploymentContext:
    """Context data needed to create a session from deployment info.

    Consumed by
    :class:`ai.backend.manager.sokovan.deployment.deployment_draft_builder.DeploymentSessionDraftBuilder`
    to assemble a :class:`SessionSpecDraft` for route-executor-driven
    inference sessions.
    """

    created_user: UserContext
    session_owner: UserContext
    container_user: ContainerUserContext
    group_id: UUID
    resource_policy: dict[str, Any]
    image: ImageContext
    resolved_presets: ResolvedPresetValues | None = None


@dataclass
class SessionDependencyData:
    """Data for session dependency relationships."""

    session_id: SessionId
    depends_on: SessionId


@dataclass
class ScalingGroupNetworkInfo:
    """Network configuration from scaling group."""

    use_host_network: bool
    wsproxy_addr: str | None = None


@dataclass
class ImageInfo:
    """Resolved image information."""

    id: UUID
    canonical: str
    architecture: str
    registry: str
    labels: dict[str, Any]
    # Resource spec maps slot names to {"min": value, "max": value}
    # Values can be strings (for BinarySize), numbers, or None
    resource_spec: dict[str, dict[str, str | int | Decimal | None]]


@dataclass
class AllowedScalingGroup:
    """Allowed scaling group for a user."""

    name: str
    is_private: bool
    scheduler_opts: ScalingGroupOpts


@dataclass
class ContainerUserInfo:
    """User container UID/GID information."""

    uid: int | None = None
    main_gid: int | None = None
    supplementary_gids: list[int] = field(default_factory=list)


@dataclass
class SessionSpecContextFetch:
    """Raw data fetched by ``ScheduleDBSource.fetch_session_spec_contexts``.

    Kept as a plain record so the repository layer does not need to
    import sokovan's scheduling-controller types (which would create a
    circular import: preparer/validator types pull data-layer types
    defined right here). The controller converts this bundle into its
    typed :class:`SessionSpecPreparationContext` +
    :class:`SessionSpecValidationContext` pair.
    """

    resource_group_defaults: Any  # DefaultSessionOptions (avoid data-layer import here)
    resource_group_network: ScalingGroupNetworkInfo | None
    container_user_info: ContainerUserInfo
    image_infos: dict[ImageID, ImageInfo]
    resource_group_allow_fractional: bool
    # Resolved vfolder mounts keyed by ``KernelGroup.role``. Each value
    # is the ``VFolderMount`` tuple the controller's batch fetch
    # materialized for that group — identical replicas share one entry,
    # and task #33 (role-based mount override) can write distinct values
    # per role without structural changes.
    vfolder_mounts_by_role: dict[str, tuple[VFolderMount, ...]]
    dotfile_data: DotfileBundle
    keypair_resource_policy: Any | None  # KeyPairResourcePolicyData
    known_slot_types: Mapping[SlotName, SlotTypes] = field(default_factory=dict)
    required_slot_names: frozenset[SlotName] = field(default_factory=frozenset)
    active_session_count: int = 0
