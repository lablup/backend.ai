from __future__ import annotations

from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import Any, AsyncIterator, Mapping, Type

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer

from ..exception import InvalidVolumeError
from ..types import VolumeInfo
from .abc import AbstractVolume


class VolumePool:
    def __init__(
        self,
        local_config: Mapping[str, Any],
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        backends: Mapping[str, Type[AbstractVolume]],
    ):
        self.local_config = local_config
        self.etcd = etcd
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.backends = backends
        self.volumes: dict[str, AbstractVolume] = {}

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {
            volume_id: VolumeInfo(**info)
            for volume_id, info in self.local_config.get("volume", {}).items()
        }

    @actxmgr
    async def get_volume(self, volume_id: str) -> AsyncIterator[AbstractVolume]:
        if volume_id in self.volumes:
            yield self.volumes[volume_id]
        else:
            try:
                volume_config = self.local_config["volume"][volume_id]
            except KeyError:
                raise InvalidVolumeError(volume_id)

            volume_cls: Type[AbstractVolume] = self.backends[volume_config["backend"]]
            volume_obj = volume_cls(
                local_config=self.local_config,
                mount_path=Path(volume_config["path"]),
                options=volume_config.get("options", {}),
                etcd=self.etcd,
                event_dispatcher=self.event_dispatcher,
                event_producer=self.event_producer,
            )

            await volume_obj.init()
            self.volumes[volume_id] = volume_obj

            yield volume_obj
