"""Type definitions for health monitoring."""

from dataclasses import dataclass
from typing import Optional

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    SessionId,
)
from ai.backend.manager.models.session import SessionStatus


@dataclass
class KernelData:
    """Kernel data for health monitoring."""

    id: KernelId
    agent: Optional[AgentId]
    image: Optional[str]
    status: str  # Kernel status
    status_changed: Optional[float]  # Timestamp when status last changed


@dataclass
class SessionData:
    """Session data for health monitoring."""

    id: SessionId
    access_key: AccessKey
    status: SessionStatus
    kernels: list[KernelData]
    main_kernel: Optional[KernelData] = None


@dataclass
class PullStatus:
    """Status of an image pull operation."""

    image: str
    is_active: bool


@dataclass
class CreationStatus:
    """Status of a kernel creation operation."""

    kernel_id: KernelId
    is_active: bool


@dataclass
class KernelHealth:
    """Health status of a running kernel."""

    kernel_id: KernelId
    is_healthy: bool
