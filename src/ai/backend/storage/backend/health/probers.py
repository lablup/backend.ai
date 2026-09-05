from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar, override

from ai.backend.storage.volumes.health.types import MountHealthRecord, MountStatus

from .abc import AbstractBackendProber
from .types import BackendProbeResult, BackendStatus


class HealthyBackendProber(AbstractBackendProber):
    """Reports an appliance that is always reachable, for volumes backed by none."""

    @override
    async def probe(self) -> BackendProbeResult:
        return BackendProbeResult(status=BackendStatus.HEALTHY, checked_at=datetime.now(UTC))


class MountDerivedBackendProber(AbstractBackendProber):
    """
    Reports the appliance of a local filesystem, which is the mount itself.

    It reads the latest mount probe rather than running one, so that it costs no system
    call and carries the time that mount was actually checked.
    """

    _STATUS_BY_MOUNT_STATUS: ClassVar[dict[MountStatus, BackendStatus]] = {
        MountStatus.ALIVE: BackendStatus.HEALTHY,
        MountStatus.DEVICE_CHANGED: BackendStatus.DEGRADED,
        MountStatus.MARKER_MISSING: BackendStatus.DEGRADED,
        MountStatus.MARKER_MISMATCH: BackendStatus.DEGRADED,
        MountStatus.HUNG: BackendStatus.OFFLINE,
        MountStatus.ERROR: BackendStatus.OFFLINE,
    }

    _record: MountHealthRecord

    def __init__(self, record: MountHealthRecord) -> None:
        self._record = record

    @override
    async def probe(self) -> BackendProbeResult:
        result = self._record.latest
        if result is None:
            return BackendProbeResult(
                status=BackendStatus.UNAVAILABLE,
                checked_at=datetime.now(UTC),
                status_info="the mount has not been probed yet",
            )
        return BackendProbeResult(
            status=self._STATUS_BY_MOUNT_STATUS[result.status],
            checked_at=result.checked_at,
            status_info=result.detail,
        )
