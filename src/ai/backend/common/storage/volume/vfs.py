from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from concurrent.futures import Executor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import override

from ai.backend.common.data.entity.storage_volume import StorageVolumeID, StorageVolumeName
from ai.backend.common.data.storage.types import VfsVolumeStatusResult
from ai.backend.common.storage.exceptions import VolumeMarkerInvalidError
from ai.backend.common.storage.probe.check import AbstractStatusCheck
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class _MountSnapshot:
    device_id: int
    marker_file_exists: bool
    marker_file_content: str


@dataclass
class VfsVolumeStatusCheckArgs:
    volume_name: StorageVolumeName
    mount_path: Path
    marker_filename: str
    executor: Executor


class VfsVolumeStatusCheck(AbstractStatusCheck[StorageVolumeName, VfsVolumeStatusResult]):
    """Reads what identifies the mount a vfs volume is served from.

    It records the mount's device id and the volume id an operator wrote in the marker
    file, and decides nothing about them: whoever reads the result compares them
    against what it expects. The mount is read in the executor it is given, so a mount
    hung in the kernel blocks a thread there and not the event loop.
    """

    _volume_name: StorageVolumeName
    _mount_path: Path
    _marker_path: Path
    _executor: Executor
    _latest: VfsVolumeStatusResult | None

    def __init__(self, args: VfsVolumeStatusCheckArgs) -> None:
        self._volume_name = args.volume_name
        self._mount_path = args.mount_path
        self._marker_path = args.mount_path / args.marker_filename
        self._executor = args.executor
        self._latest = None

    @override
    def id(self) -> StorageVolumeName:
        return self._volume_name

    @override
    def latest(self) -> VfsVolumeStatusResult | None:
        return self._latest

    @override
    async def check_status(self) -> None:
        started_at = datetime.now(UTC)
        start_counter = time.perf_counter()
        device_id: int | None = None
        marker_volume_id: StorageVolumeID | None = None
        error_msg: str | None = None
        try:
            loop = asyncio.get_running_loop()
            observed = await loop.run_in_executor(self._executor, self._read_mount)
            device_id = observed.device_id
        except OSError as e:
            log.exception(
                "volume mount cannot be read",
                volume_name=self._volume_name,
                mount_path=str(self._mount_path),
            )
            error_msg = f"{self._mount_path} cannot be read: {e}"
        except Exception as e:
            log.exception(
                "volume status check raised",
                volume_name=self._volume_name,
                mount_path=str(self._mount_path),
            )
            error_msg = str(e)
        else:
            try:
                marker_volume_id = self._parse_marker(observed)
            except VolumeMarkerInvalidError as e:
                log.warning(
                    "volume marker does not hold a volume id",
                    volume_name=self._volume_name,
                    marker_path=str(self._marker_path),
                )
                error_msg = f"{self._marker_path} does not hold a volume id: {e.extra_msg}"
        self._latest = VfsVolumeStatusResult(
            check_started_at=started_at,
            duration=timedelta(seconds=time.perf_counter() - start_counter),
            error_msg=error_msg,
            device_id=device_id,
            marker_volume_id=marker_volume_id,
        )

    def _read_mount(self) -> _MountSnapshot:
        """Reads what identifies the mount, blocking in the kernel while it does.

        ``statvfs`` is called for that blocking rather than its numbers: a dead network
        mount hangs here, which is the only signal there is that it is dead.
        """
        os.statvfs(self._mount_path)
        try:
            marker_file_content = self._marker_path.read_text().strip()
            marker_file_exists = True
        except FileNotFoundError:
            marker_file_content = ""
            marker_file_exists = False
        return _MountSnapshot(
            device_id=self._mount_path.stat().st_dev,
            marker_file_exists=marker_file_exists,
            marker_file_content=marker_file_content,
        )

    def _parse_marker(self, observed: _MountSnapshot) -> StorageVolumeID:
        if not observed.marker_file_exists:
            raise VolumeMarkerInvalidError("Marker file does not exist")
        if not observed.marker_file_content:
            raise VolumeMarkerInvalidError("Marker file is empty")
        try:
            return StorageVolumeID(uuid.UUID(observed.marker_file_content))
        except ValueError as e:
            raise VolumeMarkerInvalidError(
                f"Marker file content is not a volume id, got: {observed.marker_file_content}"
            ) from e
