from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, override

from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.data.storage.types import VfsVolumeStatusResult
from ai.backend.common.storage.probe.check import AbstractStatusCheck
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


class VfsVolumeStatusCheck(AbstractStatusCheck[StorageVolumeID, VfsVolumeStatusResult]):
    """Reads what identifies the mount a vfs volume is served from.

    It records the mount's device id and the marker file an operator writes, and decides
    nothing about them: whoever reads the result compares them against what it expects.
    """

    _volume_id: StorageVolumeID
    _mount_path: Path
    _latest: VfsVolumeStatusResult | None

    def __init__(self, args: VfsVolumeStatusCheckArgs) -> None:
        self._volume_id = args.volume_id
        self._mount_path = args.mount_path
        self._latest = None

    @override
    def id(self) -> StorageVolumeID:
        return self._volume_id

    @override
    def latest(self) -> VfsVolumeStatusResult | None:
        return self._latest

    @override
    def check_status(self) -> None:
        started_at = datetime.now(UTC)
        start_counter = time.perf_counter()
        device_id: int | None = None
        marker: str | None = None
        error_msg: str | None = None
        try:
            observed = _read_mount(self._mount_path)
            device_id = observed.device_id
            marker = observed.marker
        except OSError as e:
            log.exception(
                "volume mount cannot be read",
                volume_id=str(self._volume_id),
                mount_path=str(self._mount_path),
            )
            error_msg = f"{self._mount_path} cannot be read: {e}"
        except Exception as e:
            log.exception(
                "volume status check raised",
                volume_id=str(self._volume_id),
                mount_path=str(self._mount_path),
            )
            error_msg = str(e)
        self._latest = VfsVolumeStatusResult(
            check_started_at=started_at,
            duration=timedelta(seconds=time.perf_counter() - start_counter),
            error_msg=error_msg,
            device_id=device_id,
            marker=marker,
        )
