from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Self

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.defs import NOOP_STORAGE_VOLUME_NAME
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck
from ai.backend.common.types import VolumeID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig, VolumeInfoConfig
from ai.backend.storage.errors import InvalidVolumeError
from ai.backend.storage.types import VolumeInfo
from ai.backend.storage.watcher import WatcherClient

from .abc import AbstractVolume
from .noop import init_noop_volume

log = StructuredLogger(logging.getLogger(__spec__.name))


def _parse_volume_id(volume_name: StorageVolumeName) -> VolumeID | None:
    try:
        return VolumeID(uuid.UUID(volume_name))
    except ValueError:
        return None


class VolumePool:
    _volumes: Mapping[StorageVolumeName, AbstractVolume]
    _volumes_by_id: Mapping[VolumeID, AbstractVolume]
    _volume_status_checks: Sequence[AbstractVolumeStatusCheck]

    def __init__(self, volumes: Mapping[StorageVolumeName, AbstractVolume]) -> None:
        self._volumes = volumes
        self._volumes_by_id = {
            volume_id: volume
            for name, volume in volumes.items()
            if (volume_id := _parse_volume_id(name)) is not None
        }
        self._volume_status_checks = [
            check
            for volume in volumes.values()
            if (check := volume.volume_status_checker()) is not None
        ]

    @classmethod
    async def create(
        cls,
        local_config: StorageProxyUnifiedConfig,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        backends: Mapping[str, type[AbstractVolume]],
        watcher: WatcherClient | None = None,
    ) -> Self:
        volumes: dict[StorageVolumeName, AbstractVolume] = {}
        for volume_name, config in local_config.volume.items():
            volumes[volume_name] = await cls._init_volume(
                volume_name,
                config,
                backends[config.backend],
                local_config,
                etcd,
                event_dispatcher,
                event_producer,
                watcher,
            )
        volumes[StorageVolumeName(NOOP_STORAGE_VOLUME_NAME)] = init_noop_volume(
            etcd, event_dispatcher, event_producer
        )
        return cls(volumes=volumes)

    @classmethod
    async def _init_volume(
        cls,
        volume_name: StorageVolumeName,
        volume_config: VolumeInfoConfig,
        volume_type: type[AbstractVolume],
        local_config: StorageProxyUnifiedConfig,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        watcher: WatcherClient | None,
    ) -> AbstractVolume:
        volume_obj = volume_type(
            local_config=local_config.model_dump(by_alias=True),
            mount_path=Path(volume_config.path),
            etcd=etcd,
            event_dispatcher=event_dispatcher,
            event_producer=event_producer,
            watcher=watcher,
            options=volume_config.options or {},
            volume_name=volume_name,
            status_check_config=volume_config.volume_status_check,
        )
        await volume_obj.init()
        return volume_obj

    async def shutdown(self) -> None:
        for volume in self._volumes.values():
            await volume.shutdown()

    def volume_status_checks(self) -> Sequence[AbstractVolumeStatusCheck]:
        return self._volume_status_checks

    def list_volumes(self) -> Mapping[StorageVolumeName, VolumeInfo]:
        return {
            name: volume.info()
            for name, volume in self._volumes.items()
            if name != NOOP_STORAGE_VOLUME_NAME
        }

    def list_volumes_by_id(self) -> Mapping[VolumeID, VolumeInfo]:
        return {volume_id: volume.info() for volume_id, volume in self._volumes_by_id.items()}

    def get_volume_info(self, volume_id: VolumeID) -> VolumeInfo:
        return self.get_volume(volume_id).info()

    def get_volume(self, volume_id: VolumeID) -> AbstractVolume:
        try:
            return self._volumes_by_id[volume_id]
        except KeyError as e:
            raise InvalidVolumeError(f"Volume not found: {volume_id}") from e

    def get_volume_by_name(self, volume_name: StorageVolumeName) -> AbstractVolume:
        try:
            return self._volumes[volume_name]
        except KeyError as e:
            raise InvalidVolumeError(volume_name) from e
