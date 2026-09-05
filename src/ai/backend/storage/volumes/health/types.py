from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal

# Read by the mount probe and written only by `backend.ai storage volume mark`.
MARKER_FILE_NAME: Final = ".backend.ai-volume"


class MountStatus(enum.StrEnum):
    """Outcome of a mount probe on a single volume."""

    ALIVE = "alive"
    DEVICE_CHANGED = "device-changed"
    MARKER_MISSING = "marker-missing"
    MARKER_MISMATCH = "marker-mismatch"
    HUNG = "hung"
    ERROR = "error"


@dataclass(frozen=True)
class MountProbeResult:
    """The latest mount probe outcome for one volume."""

    status: MountStatus
    checked_at: datetime
    detail: str | None = None
    device_id: int | None = None


class BackendStatus(enum.StrEnum):
    """Reachability of a backend appliance, mirroring the hardware metadata statuses."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"

    def to_hwinfo_status(self) -> Literal["healthy", "degraded", "offline", "unavailable"]:
        match self:
            case BackendStatus.HEALTHY:
                return "healthy"
            case BackendStatus.DEGRADED:
                return "degraded"
            case BackendStatus.OFFLINE:
                return "offline"
            case BackendStatus.UNAVAILABLE:
                return "unavailable"


@dataclass(frozen=True)
class BackendProbeResult:
    """The latest reachability of one volume's backend appliance from this proxy."""

    status: BackendStatus
    checked_at: datetime
    status_info: str | None = None


@dataclass
class VolumeHealthRecord:
    """
    Where one volume's probe loops record their latest results.

    A None field means the corresponding probe has not run yet, which the manager tells
    apart from a stale result by the check time each result carries.
    """

    mount: MountProbeResult | None = None
    backend: BackendProbeResult | None = None
