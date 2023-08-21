from __future__ import annotations

from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import Any, AsyncIterator, Mapping, Type

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.storage.weka import WekaVolume

from .abc import AbstractVolume
from .cephfs import CephFSVolume
from .dellemc import DellEMCOneFSVolume
from .exception import InvalidVolumeError
from .gpfs import GPFSVolume
from .kmanila import KManilaFSVolume
from .netapp import NetAppVolume
from .purestorage import FlashBladeVolume
from .types import VolumeInfo
from .vfs import BaseVolume
from .xfs import XfsVolume

BACKENDS: Mapping[str, Type[AbstractVolume]] = {
    "purestorage": FlashBladeVolume,
    "vfs": BaseVolume,
    "xfs": XfsVolume,
    "netapp": NetAppVolume,
    # NOTE: Dell EMC has two different storage: PowerStore and PowerScale (OneFS).
    #       We support the latter only for now.
    "dellemc-onefs": DellEMCOneFSVolume,
    "weka": WekaVolume,
    "gpfs": GPFSVolume,  # IBM SpectrumScale or GPFS
    "spectrumscale": GPFSVolume,  # IBM SpectrumScale or GPFS
    "cephfs": CephFSVolume,
    "kmanila": KManilaFSVolume,
}


class BaseContext:
    __slots__ = ("pid", "etcd", "local_config", "dsn")

    pid: int
    etcd: AsyncEtcd
    local_config: Mapping[str, Any]
    dsn: str | None

    def __init__(
        self,
        pid: int,
        local_config: Mapping[str, Any],
        etcd: AsyncEtcd,
        *,
        dsn: str | None = None,
    ) -> None:
        self.pid = pid
        self.etcd = etcd
        self.local_config = local_config
        self.dsn = dsn

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {name: VolumeInfo(**info) for name, info in self.local_config["volume"].items()}

    @actxmgr
    async def get_volume(self, name: str) -> AsyncIterator[AbstractVolume]:
        try:
            volume_config = self.local_config["volume"][name]
        except KeyError:
            raise InvalidVolumeError(name)
        volume_cls: Type[AbstractVolume] = BACKENDS[volume_config["backend"]]
        volume_obj = volume_cls(
            local_config=self.local_config,
            mount_path=Path(volume_config["path"]),
            options=volume_config["options"] or {},
            etcd=self.etcd,
        )
        await volume_obj.init()
        try:
            yield volume_obj
        finally:
            await volume_obj.shutdown()


class Context(BaseContext):
    __slots__ = ("pid", "etcd", "local_config", "dsn", "event_producer", "event_dispatcher")

    event_producer: EventProducer
    event_dispatcher: EventDispatcher

    def __init__(
        self,
        pid: int,
        local_config: Mapping[str, Any],
        etcd: AsyncEtcd,
        event_producer: EventProducer,
        event_dispatcher: EventDispatcher,
        *,
        dsn: str | None = None,
    ) -> None:
        super().__init__(pid, local_config, etcd, dsn=dsn)
        self.event_producer = event_producer
        self.event_dispatcher = event_dispatcher
