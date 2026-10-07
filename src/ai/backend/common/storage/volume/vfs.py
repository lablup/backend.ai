from __future__ import annotations

import os
from concurrent.futures import Executor
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Self, override

from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.exception import StorageVolumeUnusableError
from ai.backend.common.storage.volume.abc import AbstractVolumeStatusCheck

VOLUME_MARKER_FILENAME: Final = ".backend.ai-volume-id"


@dataclass
class _MountSnapshot:
    device_id: int
    marker: str | None


def _read_mount(mount_path: Path) -> _MountSnapshot:
    """Reads what identifies the mount, blocking in the kernel while it does.

    ``statvfs`` is called for that blocking rather than its numbers: a dead network
    mount hangs here, and the caller's timeout is the only signal there is.
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
    executor: Executor


class VfsVolumeStatusCheck(AbstractVolumeStatusCheck[None]):
    """Whether the one mount a vfs volume is served from is still the mount it started on.

    Compares the device id against the value captured at startup and reads the marker
    file an operator writes, raising the reason rather than returning a verdict.
    """

    _volume_id: StorageVolumeID
    _mount_path: Path
    _executor: Executor
    _baseline: _MountSnapshot | None

    def __init__(self, args: VfsVolumeStatusCheckArgs, baseline: _MountSnapshot | None) -> None:
        self._volume_id = args.volume_id
        self._mount_path = args.mount_path
        self._executor = args.executor
        self._baseline = baseline

    @classmethod
    async def create(cls, args: VfsVolumeStatusCheckArgs) -> Self:
        """Captures what the mount looks like now, for later checks to compare against.

        A mount that cannot be read yet leaves the baseline unset, so a dead mount
        reports itself through the probe loop instead of holding up the service.
        """
        try:
            baseline = await run_in_executor_with_context(
                args.executor, _read_mount, args.mount_path
            )
        except OSError:
            baseline = None
        return cls(args, baseline)

    @property
    @override
    def volume_id(self) -> StorageVolumeID:
        return self._volume_id

    @override
    async def check_status(self) -> None:
        try:
            current = await run_in_executor_with_context(
                self._executor, _read_mount, self._mount_path
            )
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
