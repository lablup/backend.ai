from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.cron.local_cron import LocalCron
from ai.backend.common.data.storage.types import VolumeName

from .abc import AbstractBackendProber, AbstractMountProber
from .tasks import BackendProbeTask, MountProbeTask
from .types import VolumeHealthRecord

if TYPE_CHECKING:
    from ai.backend.storage.config.unified import VolumeHealthConfig


class VolumeHealthProbes:
    """
    Owns one volume's probe loops, started and stopped with the volume itself.

    The mount and the backend run on separate loops, both independent of the heartbeat,
    so that a slow or hung probe never delays a heartbeat.
    """

    _mount_task: MountProbeTask
    _cron: LocalCron

    def __init__(
        self,
        volume_name: VolumeName,
        record: VolumeHealthRecord,
        config: VolumeHealthConfig,
        mount_prober: AbstractMountProber,
        backend_prober: AbstractBackendProber,
    ) -> None:
        self._mount_task = MountProbeTask(
            volume_name,
            mount_prober,
            record,
            interval=config.mount_probe_interval,
            timeout=config.mount_probe_timeout,
        )
        self._cron = LocalCron([
            self._mount_task,
            BackendProbeTask(
                volume_name,
                backend_prober,
                record,
                interval=config.backend_probe_interval,
                timeout=config.backend_probe_timeout,
            ),
        ])

    async def start(self) -> None:
        await self._cron.start()

    async def stop(self) -> None:
        await self._cron.stop()
        self._mount_task.shutdown()
