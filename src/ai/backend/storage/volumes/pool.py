from __future__ import annotations

import logging
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import AsyncIterator, Mapping, Self, Type

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import VolumeID
from ai.backend.logging import BraceStyleAdapter

from ..config.unified import StorageProxyUnifiedConfig, VolumeInfoConfig
from ..exception import InvalidVolumeError
from ..plugin import StoragePluginContext
from ..types import VolumeInfo
from .abc import AbstractVolume
from .cephfs import CephFSVolume
from .ddn import EXAScalerFSVolume
from .dellemc import DellEMCOneFSVolume
from .gpfs import GPFSVolume
from .netapp import NetAppVolume
from .purestorage import FlashBladeVolume
from .vast import VASTVolume
from .vfs import BaseVolume
from .weka import WekaVolume
from .xfs import XfsVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_BACKENDS: Mapping[str, Type[AbstractVolume]] = {
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
    _volumes: Mapping[VolumeID, AbstractVolume]
    _volumes_by_name: Mapping[str, AbstractVolume]
    _storage_backend_plugin_ctx: StoragePluginContext

    def __init__(
        self,
        volumes: Mapping[VolumeID, AbstractVolume],
        volumes_by_name: Mapping[str, AbstractVolume],
        storage_backend_plugin_ctx: StoragePluginContext,
    ) -> None:
        self._volumes = volumes
        self._volumes_by_name = volumes_by_name
        self._storage_backend_plugin_ctx = storage_backend_plugin_ctx

    @classmethod
    async def create(
        cls,
        local_config: StorageProxyUnifiedConfig,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
    ) -> Self:
        backends = {**_DEFAULT_BACKENDS}
        storage_backend_plugin_ctx = await cls._init_storage_backend_plugin(
            backends, local_config, etcd
        )

        volumes: dict[VolumeID, AbstractVolume] = {}
        volumes_by_name: dict[str, AbstractVolume] = {}
        for raw_volume_id, config in local_config.volume.items():
            try:
                volume_id = VolumeID(raw_volume_id)
            except (ValueError, TypeError):
                volumes_by_name[raw_volume_id] = await cls._init_volume(
                    config,
                    backends[config.backend],
                    local_config,
                    etcd,
                    event_dispatcher,
                    event_producer,
                )
            else:
                volumes[volume_id] = await cls._init_volume(
                    config,
                    backends[config.backend],
                    local_config,
                    etcd,
                    event_dispatcher,
                    event_producer,
                )
        return cls(
            volumes=volumes,
            volumes_by_name=volumes_by_name,
            storage_backend_plugin_ctx=storage_backend_plugin_ctx,
        )

    @classmethod
    async def _init_volume(
        cls,
        volume_config: VolumeInfoConfig,
        volume_type: Type[AbstractVolume],
        local_config: StorageProxyUnifiedConfig,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
    ) -> AbstractVolume:
        volume_obj = volume_type(
            local_config=local_config.model_dump(by_alias=True),
            mount_path=Path(volume_config.path),
            etcd=etcd,
            event_dispatcher=event_dispatcher,
            event_producer=event_producer,
            options=volume_config.options or {},
        )
        await volume_obj.init()
        return volume_obj

    @classmethod
    async def _init_storage_backend_plugin(
        cls,
        backends: dict[str, Type[AbstractVolume]],
        local_config: StorageProxyUnifiedConfig,
        etcd: AsyncEtcd,
    ) -> StoragePluginContext:
        plugin_ctx = StoragePluginContext(etcd, local_config.model_dump())
        await plugin_ctx.init()
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            log.info("Loading storage plugin: {0}", plugin_name)
            volume_cls = plugin_instance.get_volume_class()
            backends[plugin_name] = volume_cls
        return plugin_ctx

    async def shutdown(self) -> None:
        for volume in self._volumes.values():
            await volume.shutdown()
        await self._storage_backend_plugin_ctx.cleanup()

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {str(volume_id): volume.info() for volume_id, volume in self._volumes.items()}

    def get_volume_info(self, volume_id: VolumeID) -> VolumeInfo:
        if volume_id not in self._volumes:
            raise InvalidVolumeError(f"Volume not found: {volume_id}")
        return self._volumes[volume_id].info()

    @actxmgr
    async def get_volume(self, volume_id: VolumeID) -> AsyncIterator[AbstractVolume]:
        try:
            yield self._volumes[volume_id]
        except KeyError:
            raise InvalidVolumeError(f"Volume not found: {volume_id}")

    @actxmgr
    async def get_volume_by_name(self, name: str) -> AsyncIterator[AbstractVolume]:
        try:
            yield self._volumes_by_name[name]
        except KeyError:
            raise InvalidVolumeError(name)
