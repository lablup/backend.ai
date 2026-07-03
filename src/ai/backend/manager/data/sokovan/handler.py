"""Session/kernel data passed to scheduler lifecycle handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus


@dataclass
class HandlerKernelData:
    """Kernel data for handler execution.

    Contains minimal kernel information needed by handlers.
    """

    kernel_id: UUID
    agent_id: AgentId | None
    status: KernelStatus
    container_id: str | None = None
    occupied_slots: ResourceSlot | None = None


@dataclass
class HandlerSessionData:
    """Session data passed to handlers by coordinator.

    Contains all necessary information for handler execution
    without requiring additional database queries for basic operations.
    """

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    status: SessionStatus
    scaling_group: str
    session_type: SessionTypes
    status_info: str | None = None
    kernels: list[HandlerKernelData] = field(default_factory=list)
