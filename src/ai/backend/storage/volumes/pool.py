from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Self

from ai.backend.common.defs import NOOP_STORAGE_VOLUME_NAME
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import VolumeID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig, VolumeInfoConfig
from ai.backend.storage.errors import InvalidVolumeError
from ai.backend.storage.types import VolumeInfo
from ai.backend.storage.watcher import WatcherClient

from .abc import AbstractVolume
from .noop import init_noop_volume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _parse_volume_id(raw_key: str) -> VolumeID | None:
    try:
        return VolumeID(uuid.UUID(raw_key))
    except (ValueError, TypeError):
        return None


def _volume_key(raw_key: str) -> str:
    volume_id = _parse_volume_id(raw_key)
    return raw_key if volume_id is None else str(volume_id)


class VolumePool:
    _volumes: Mapping[str, AbstractVolume]

    def __init__(self, volumes: Mapping[str, AbstractVolume]) -> None:
        self._volumes = volumes

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
        volumes: dict[str, AbstractVolume] = {}
        for raw_volume_id, config in local_config.volume.items():
            volumes[_volume_key(raw_volume_id)] = await cls._init_volume(
                config,
                backends[config.backend],
                local_config,
                etcd,
                event_dispatcher,
                event_producer,
                watcher,
            )
        volumes[NOOP_STORAGE_VOLUME_NAME] = init_noop_volume(etcd, event_dispatcher, event_producer)
        return cls(volumes=volumes)

    @classmethod
    async def _init_volume(
        cls,
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
        )
        await volume_obj.init()
        return volume_obj

    async def shutdown(self) -> None:
        for volume in self._volumes.values():
            await volume.shutdown()

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {
            key: volume.info()
            for key, volume in self._volumes.items()
            if _parse_volume_id(key) is not None
        }

    def get_volume_info(self, volume_id: VolumeID) -> VolumeInfo:
        return self.get_volume(volume_id).info()

    def get_volume(self, volume_id: VolumeID) -> AbstractVolume:
        try:
            return self._volumes[str(volume_id)]
        except KeyError as e:
            raise InvalidVolumeError(f"Volume not found: {volume_id}") from e

    def get_volume_by_name(self, name: str) -> AbstractVolume:
        try:
            return self._volumes[_volume_key(name)]
        except KeyError as e:
            raise InvalidVolumeError(name) from e
