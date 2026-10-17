from __future__ import annotations

import asyncio
import inspect
import json
import logging
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, override

from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.data.storage.types import VfsVolumeStatusResult
from ai.backend.common.storage.abc import AbstractStatusCheck
from ai.backend.common.storage.exceptions import (
    VolumeMarkerInvalidError,
    VolumeMountUnreadableError,
)
from ai.backend.common.storage.volume import vfs_mount_reader
from ai.backend.common.storage.volume.vfs_mount_reader import MountSnapshot
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_MOUNT_READER_SOURCE: Final = inspect.getsource(vfs_mount_reader)


@dataclass
class VfsVolumeStatusCheckArgs:
    volume_id: StorageVolumeID
    mount_path: Path
    marker_filename: str


class VfsVolumeStatusCheck(AbstractStatusCheck[StorageVolumeID, VfsVolumeStatusResult]):
    """Reads what identifies the mount a vfs volume is served from.

    It records the mount's device id and the volume id an operator wrote in the marker
    file, and decides nothing about them: whoever reads the result compares them
    against what it expects.
    """

    _volume_id: StorageVolumeID
    _mount_path: Path
    _marker_path: Path
    _latest: VfsVolumeStatusResult | None

    def __init__(self, args: VfsVolumeStatusCheckArgs) -> None:
        self._volume_id = args.volume_id
        self._mount_path = args.mount_path
        self._marker_path = args.mount_path / args.marker_filename
        self._latest = None

    @override
    def id(self) -> StorageVolumeID:
        return self._volume_id

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
            observed = await self._read_mount()
            device_id = observed.device_id
        except VolumeMountUnreadableError as e:
            log.exception(
                "volume mount cannot be read",
                volume_id=str(self._volume_id),
                mount_path=str(self._mount_path),
            )
            error_msg = f"{self._mount_path} cannot be read: {e.extra_msg}"
        except Exception as e:
            log.exception(
                "volume status check raised",
                volume_id=str(self._volume_id),
                mount_path=str(self._mount_path),
            )
            error_msg = str(e)
        else:
            try:
                marker_volume_id = self._parse_marker(observed.marker_file_content)
            except VolumeMarkerInvalidError as e:
                log.warning(
                    "volume marker does not hold a volume id",
                    volume_id=str(self._volume_id),
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

    async def _read_mount(self) -> MountSnapshot:
        """Runs the mount read in a child process so a hung mount blocks only that process."""
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-I",
            "-c",
            _MOUNT_READER_SOURCE,
            str(self._mount_path),
            str(self._marker_path),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await proc.communicate()
        except asyncio.CancelledError:
            if proc.returncode is None:
                proc.kill()
            raise
        if proc.returncode != 0:
            raise VolumeMountUnreadableError(stderr.decode().strip())
        return MountSnapshot(**json.loads(stdout))

    def _parse_marker(self, marker_file_content: str | None) -> StorageVolumeID:
        if marker_file_content is None:
            raise VolumeMarkerInvalidError("Marker file content is None")
        try:
            return StorageVolumeID(uuid.UUID(marker_file_content))
        except (ValueError, TypeError) as e:
            raise VolumeMarkerInvalidError(
                f"Marker file content is invalid, got: {marker_file_content}"
            ) from e
