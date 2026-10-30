from __future__ import annotations

import asyncio
import logging
import os
import time
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Self, override

from ai.backend.common.configs.volume_status_check import VolumeStatusCheckConfig
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageAnomaly,
    StorageCheckState,
    StorageStatusCheckType,
    StorageStatusResultData,
)
from ai.backend.common.storage.probe.anomaly import AbstractStatusAnomalyDetector
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class VfsVolumeStatusCheckArgs:
    volume_name: StorageVolumeName
    mount_path: Path
    interval: float
    initial_delay: float
    executor: Executor


class VfsVolumeAnomalyDetector(AbstractStatusAnomalyDetector):
    """Detects an anomaly in a vfs volume's result."""

    @override
    def detect(
        self, latest: StorageStatusResultData | None, current: StorageStatusResultData
    ) -> StorageAnomaly:
        """Detected when the mount could not be read, or when its device id differs from
        the latest one read, as a mount that fell off serves the parent filesystem."""
        if current.check_state == StorageCheckState.NOT_CHECKED:
            return StorageAnomaly.NONE
        if current.error_msg is not None or current.device_id is None:
            return StorageAnomaly.DETECTED
        if (
            latest is not None
            and latest.device_id is not None
            and latest.device_id != current.device_id
        ):
            return StorageAnomaly.DETECTED
        return StorageAnomaly.NONE


class VfsVolumeStatusCheck(AbstractVolumeStatusCheck):
    """Reads the device id of the mount a vfs volume is served from.

    The mount is read in the executor it is given, so a mount hung in the kernel blocks
    a thread there and not the event loop.
    """

    _volume_name: StorageVolumeName
    _mount_path: Path
    _interval: float
    _initial_delay: float
    _executor: Executor
    _latest: StorageStatusResultData

    def __init__(self, args: VfsVolumeStatusCheckArgs) -> None:
        self._volume_name = args.volume_name
        self._mount_path = args.mount_path
        self._interval = args.interval
        self._initial_delay = args.initial_delay
        self._executor = args.executor
        self._latest = StorageStatusResultData(
            check_type=StorageStatusCheckType.VFS,
            check_state=StorageCheckState.NOT_CHECKED,
            check_started_at=None,
            duration=None,
            error_msg=None,
            device_id=None,
            extra=None,
        )

    @classmethod
    def create(
        cls,
        volume_name: StorageVolumeName,
        mount_path: Path,
        config: VolumeStatusCheckConfig,
    ) -> Self:
        return cls(
            VfsVolumeStatusCheckArgs(
                volume_name=volume_name,
                mount_path=mount_path,
                interval=config.check_interval,
                initial_delay=config.initial_delay,
                executor=ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix=f"vfs-volume-status-{volume_name}"
                ),
            )
        )

    @override
    def id(self) -> StorageVolumeName:
        return self._volume_name

    @override
    def interval(self) -> float:
        return self._interval

    @override
    def initial_delay(self) -> float:
        return self._initial_delay

    @override
    def latest(self) -> StorageStatusResultData:
        return self._latest

    @override
    async def check_status(self) -> None:
        started_at = datetime.now(UTC)
        start_counter = time.perf_counter()
        device_id: str | None = None
        error_msg: str | None = None
        try:
            loop = asyncio.get_running_loop()
            device_id = str(await loop.run_in_executor(self._executor, self._read_device_id))
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
        self._latest = StorageStatusResultData(
            check_type=StorageStatusCheckType.VFS,
            check_state=StorageCheckState.CHECKED,
            check_started_at=started_at,
            duration=timedelta(seconds=time.perf_counter() - start_counter),
            error_msg=error_msg,
            device_id=device_id,
            extra=None,
        )

    def _read_device_id(self) -> int:
        """Reads the mount's device id, blocking in the kernel while it does.

        ``statvfs`` is called for that blocking rather than its numbers: a dead network
        mount hangs here, which is the only signal there is that it is dead.
        """
        os.statvfs(self._mount_path)
        return self._mount_path.stat().st_dev
