from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


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
class BackendHealthRecord:
    """
    Where one backend appliance's probe loop records its latest result.

    A None result means the probe has not run yet, which the manager tells apart from a
    stale result by the check time each result carries.
    """

    latest: BackendProbeResult | None = None
