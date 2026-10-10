from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, override

from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.data.storage.types import StorageStatusResult
from ai.backend.common.exception import BackendAIError, StorageVolumeUnusableError
from ai.backend.common.storage.abc import AbstractStatusCheck
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

VOLUME_MARKER_FILENAME: Final = ".backend.ai-volume-id"


@dataclass
class _MountSnapshot:
    device_id: int
    marker: str | None


def _read_mount(mount_path: Path) -> _MountSnapshot:
    """Reads what identifies the mount, blocking in the kernel while it does.

    ``statvfs`` is called for that blocking rather than its numbers: a dead network
    mount hangs here, which is the only signal there is that it is dead.
    """
    os.statvfs(mount_path)
    marker_path = mount_path / VOLUME_MARKER_FILENAME
    try:
        marker = marker_path.read_text().strip()
    except FileNotFoundError:
        marker = None
    return _MountSnapshot(device_id=mount_path.stat().st_dev, marker=marker)


@dataclass
class VfsVolumeStatusCheckArgs:
    volume_id: StorageVolumeID
    mount_path: Path


class VfsVolumeStatusCheck(AbstractStatusCheck[StorageVolumeID]):
    """Whether the one mount a vfs volume is served from is still the mount it started on.

    Compares the device id against the value the first check read and reads the marker
    file an operator writes.
    """

    _volume_id: StorageVolumeID
    _mount_path: Path
    _baseline: _MountSnapshot | None
    _latest: StorageStatusResult | None

    def __init__(self, args: VfsVolumeStatusCheckArgs) -> None:
        self._volume_id = args.volume_id
        self._mount_path = args.mount_path
        self._baseline = None
        self._latest = None

    @override
    def get_id(self) -> StorageVolumeID:
        return self._volume_id

    @override
    def get_latest(self) -> StorageStatusResult | None:
        return self._latest

    @override
    def check_status(self) -> None:
        started_at = datetime.now(UTC)
        start_counter = time.perf_counter()
        error_msg: str | None = None
        try:
            self._verify_mount()
        except BackendAIError as e:
            error_msg = e.extra_msg or str(e)
        except Exception as e:
            log.exception("volume status check raised", volume_id=str(self._volume_id))
            error_msg = str(e)
        self._latest = StorageStatusResult(
            check_started_at=started_at,
            duration=timedelta(seconds=time.perf_counter() - start_counter),
            error_msg=error_msg,
        )

    def _verify_mount(self) -> None:
        try:
            current = _read_mount(self._mount_path)
        except OSError as e:
            raise StorageVolumeUnusableError(
                extra_msg=f"{self._mount_path} cannot be read: {e}"
            ) from e
        baseline = self._baseline
        if baseline is None:
            self._baseline = current
            baseline = current
        if current.device_id != baseline.device_id:
            raise StorageVolumeUnusableError(
                extra_msg=(
                    f"{self._mount_path} is on device {current.device_id}, "
                    f"not the {baseline.device_id} it was mounted on"
                )
            )
        if baseline.marker is not None and current.marker is None:
            raise StorageVolumeUnusableError(
                extra_msg=f"the volume marker under {self._mount_path} is gone"
            )
        if current.marker is not None and current.marker != str(self._volume_id):
            raise StorageVolumeUnusableError(
                extra_msg=f"{self._mount_path} is marked as volume {current.marker}"
            )
