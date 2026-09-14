from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import Self

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import VolumeID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig, VolumeInfoConfig
from ai.backend.storage.errors import InvalidVolumeError
from ai.backend.storage.types import VolumeInfo

from .abc import AbstractVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VolumePool:
    _volumes: Mapping[VolumeID, AbstractVolume]
    _volumes_by_name: Mapping[str, AbstractVolume]

    def __init__(
        self,
        volumes: Mapping[VolumeID, AbstractVolume],
        volumes_by_name: Mapping[str, AbstractVolume],
    ) -> None:
        self._volumes = volumes
        self._volumes_by_name = volumes_by_name

    @classmethod
    async def create(
        cls,
        local_config: StorageProxyUnifiedConfig,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        backends: Mapping[str, type[AbstractVolume]],
    ) -> Self:
        volumes: dict[VolumeID, AbstractVolume] = {}
        volumes_by_name: dict[str, AbstractVolume] = {}
        for raw_volume_id, config in local_config.volume.items():
            try:
                volume_id = VolumeID(uuid.UUID(raw_volume_id))
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
        )

    @classmethod
    async def _init_volume(
        cls,
        volume_config: VolumeInfoConfig,
        volume_type: type[AbstractVolume],
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

    async def shutdown(self) -> None:
        for volume in self._volumes.values():
            await volume.shutdown()

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
        except KeyError as e:
            raise InvalidVolumeError(f"Volume not found: {volume_id}") from e

    @actxmgr
    async def get_volume_by_name(self, name: str) -> AsyncIterator[AbstractVolume]:
        try:
            yield self._volumes_by_name[name]
        except KeyError as e:
            raise InvalidVolumeError(name) from e

    def get_volume_by_name_direct(self, name: str) -> AbstractVolume:
        """Get volume by name without context manager."""
        try:
            return self._volumes_by_name[name]
        except KeyError as e:
            raise InvalidVolumeError(name) from e
