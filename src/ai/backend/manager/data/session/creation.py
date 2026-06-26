"""Shared value objects for session creation and scheduling.

These types are produced by the repository layer (from ORM rows) and
consumed by the sokovan scheduling controller. They live in ``data/`` so
neither side has to import the other's package.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AccessKey


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
class ContainerUserInfo:
    """User container UID/GID information."""

    uid: int | None = None
    main_gid: int | None = None
    supplementary_gids: list[int] = field(default_factory=list)
