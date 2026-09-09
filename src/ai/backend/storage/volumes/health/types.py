from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Final

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


@dataclass
class MountHealthRecord:
    """
    Where one volume's mount probe loop records its latest result.

    A None result means the probe has not run yet, which the manager tells apart from a
    stale result by the check time each result carries.
    """

    latest: MountProbeResult | None = None
