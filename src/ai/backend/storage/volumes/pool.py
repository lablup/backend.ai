from __future__ import annotations

from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import Any, AsyncIterator, Mapping, Type

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.storage.volumes.cephfs import CephFSVolume
from ai.backend.storage.volumes.ddn import EXAScalerFSVolume
from ai.backend.storage.volumes.dellemc import DellEMCOneFSVolume
from ai.backend.storage.volumes.gpfs import GPFSVolume
from ai.backend.storage.volumes.netapp import NetAppVolume
from ai.backend.storage.volumes.purestorage import FlashBladeVolume
from ai.backend.storage.volumes.vast import VASTVolume
from ai.backend.storage.volumes.vfs import BaseVolume
from ai.backend.storage.volumes.weka import WekaVolume
from ai.backend.storage.volumes.xfs import XfsVolume

from ..exception import InvalidVolumeError
from ..types import VolumeInfo
from .abc import AbstractVolume

DEFAULT_BACKENDS: Mapping[str, Type[AbstractVolume]] = {
    FlashBladeVolume.name: FlashBladeVolume,
    BaseVolume.name: BaseVolume,
    XfsVolume.name: XfsVolume,
    NetAppVolume.name: NetAppVolume,
    # NOTE: Dell EMC has two different storage: PowerStore and PowerScale (OneFS).
    #       We support the latter only for now.
    DellEMCOneFSVolume.name: DellEMCOneFSVolume,
    WekaVolume.name: WekaVolume,
    GPFSVolume.name: GPFSVolume,  # IBM SpectrumScale or GPFS
    "spectrumscale": GPFSVolume,  # IBM SpectrumScale or GPFS
    CephFSVolume.name: CephFSVolume,
    VASTVolume.name: VASTVolume,
    EXAScalerFSVolume.name: EXAScalerFSVolume,
}


class VolumePool:
    _volumes: dict[str, AbstractVolume]
    _local_config: Mapping[str, Any]
    _etcd: AsyncEtcd
    _event_dispatcher: EventDispatcher
    _event_producer: EventProducer
    _backends: dict[str, Type[AbstractVolume]]

    def __init__(
        self,
        local_config: Mapping[str, Any],
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
    ):
        self._volumes = {}
        self._local_config = local_config
        self._etcd = etcd
        self._event_dispatcher = event_dispatcher
        self._event_producer = event_producer

    async def __aenter__(self) -> None:
        self._backends = {**DEFAULT_BACKENDS}

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {
            volume_id: VolumeInfo(**info)
            for volume_id, info in self._local_config["volume"].items()
        }

    @actxmgr
    async def get_volume(self, volume_id: str) -> AsyncIterator[AbstractVolume]:
        if volume_id in self._volumes:
            yield self._volumes[volume_id]
        else:
            try:
                volume_config = self._local_config["volume"][volume_id]
            except KeyError:
                raise InvalidVolumeError(volume_id)

            volume_cls: Type[AbstractVolume] = self._backends[volume_config["backend"]]
            volume_obj = volume_cls(
                local_config=self._local_config,
                mount_path=Path(volume_config["path"]),
                etcd=self._etcd,
                event_dispatcher=self._event_dispatcher,
                event_producer=self._event_producer,
                options=volume_config["options"] or {},
            )

            await volume_obj.init()
            self._volumes[volume_id] = volume_obj

            yield volume_obj
