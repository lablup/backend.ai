from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from ai.backend.common.data.storage.types import VolumeName

from .abc import AbstractMountProber
from .types import MARKER_FILE_NAME, MountProbeResult, MountStatus


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
