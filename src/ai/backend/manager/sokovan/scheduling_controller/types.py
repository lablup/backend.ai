"""Types for session controller."""

from dataclasses import dataclass
from typing import Any

from ai.backend.common.types import ResourceSlot


@dataclass
class KernelResourceInfo:
    """Calculated resource information for a kernel."""

    requested_slots: ResourceSlot
    resource_opts: dict[str, Any]


@dataclass
class CalculatedResources:
    """Pre-calculated resources for session creation."""

    session_requested_slots: ResourceSlot
    kernel_resources: list[KernelResourceInfo]
