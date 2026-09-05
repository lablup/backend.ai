from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, override

from ai.backend.common.data.storage.types import VolumeName

from .abc import AbstractBackendProber, AbstractMountProber
from .types import (
    MARKER_FILE_NAME,
    BackendProbeResult,
    BackendStatus,
    MountProbeResult,
    MountStatus,
    VolumeHealthRecord,
)


class PathMountProber(AbstractMountProber):
    """
    Checks a mount point by its device id, its filesystem statistics and its marker file.

    The device id baseline cannot survive a restart, because the kernel assigns a device
    number at mount time; the marker file is the check that does.
    """

    _volume_name: VolumeName
    _mount_path: Path
    _device_id: int | None
    _marker_present_at_init: bool

    def __init__(self, volume_name: VolumeName, mount_path: Path) -> None:
        self._volume_name = volume_name
        self._mount_path = mount_path
        self._device_id = None
        self._marker_present_at_init = False

    @override
    def capture_baseline(self) -> None:
        self._device_id = self._mount_path.stat().st_dev
        self._marker_present_at_init = (self._mount_path / MARKER_FILE_NAME).exists()

    @override
    def probe(self) -> MountProbeResult:
        now = datetime.now(UTC)
        try:
            device_id = self._mount_path.stat().st_dev
            if self._device_id is not None and device_id != self._device_id:
                return MountProbeResult(
                    status=MountStatus.DEVICE_CHANGED,
                    checked_at=now,
                    detail=f"the device id changed from {self._device_id} to {device_id}",
                    device_id=device_id,
                )
            os.statvfs(self._mount_path)
            status, detail = self._check_marker()
        except OSError as e:
            return MountProbeResult(status=MountStatus.ERROR, checked_at=now, detail=str(e))
        if self._device_id is None:
            # The baseline capture at startup failed; adopt the first value we could read.
            self._device_id = device_id
        return MountProbeResult(status=status, checked_at=now, detail=detail, device_id=device_id)

    def _check_marker(self) -> tuple[MountStatus, str | None]:
        try:
            declared = (self._mount_path / MARKER_FILE_NAME).read_text().strip()
        except FileNotFoundError:
            if self._marker_present_at_init:
                return MountStatus.MARKER_MISSING, "the volume marker disappeared after startup"
            return MountStatus.ALIVE, "the volume marker is absent; identity is unverified"
        if declared != self._volume_name:
            return MountStatus.MARKER_MISMATCH, f"the volume marker declares {declared!r}"
        return MountStatus.ALIVE, None


class AliveMountProber(AbstractMountProber):
    """Reports a mount that always answers, for volumes backed by no real mount."""

    @override
    def probe(self) -> MountProbeResult:
        return MountProbeResult(status=MountStatus.ALIVE, checked_at=datetime.now(UTC))


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

    _record: VolumeHealthRecord

    def __init__(self, record: VolumeHealthRecord) -> None:
        self._record = record

    @override
    async def probe(self) -> BackendProbeResult:
        result = self._record.mount
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


class HealthyBackendProber(AbstractBackendProber):
    """Reports an appliance that is always reachable, for volumes backed by none."""

    @override
    async def probe(self) -> BackendProbeResult:
        return BackendProbeResult(status=BackendStatus.HEALTHY, checked_at=datetime.now(UTC))
