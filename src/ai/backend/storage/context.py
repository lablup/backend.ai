from __future__ import annotations

import logging
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Final,
    Mapping,
    Optional,
    Type,
)

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.logging import BraceStyleAdapter

from .abc import AbstractVolume
from .cephfs import CephFSVolume
from .dellemc import DellEMCOneFSVolume
from .exception import InvalidVolumeError
from .gpfs import GPFSVolume
from .netapp import NetAppVolume
from .plugin import StoragePluginContext
from .purestorage import FlashBladeVolume
from .types import VolumeInfo
from .vfs import BaseVolume
from .weka import WekaVolume
from .xfs import XfsVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "storage-proxy"

DEFAULT_BACKENDS: Mapping[str, Type[AbstractVolume]] = {
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
}


class RootContext:
    pid: int
    etcd: AsyncEtcd
    local_config: Mapping[str, Any]
    dsn: str | None
    event_producer: EventProducer
    event_dispatcher: EventDispatcher

    def __init__(
        self,
        pid: int,
        local_config: Mapping[str, Any],
        etcd: AsyncEtcd,
        *,
        event_producer: EventProducer,
        event_dispatcher: EventDispatcher,
        dsn: Optional[str] = None,
    ) -> None:
        self.pid = pid
        self.etcd = etcd
        self.local_config = local_config
        self.dsn = dsn
        self.event_producer = event_producer
        self.event_dispatcher = event_dispatcher

    async def __aenter__(self) -> None:
        plugin_ctx = StoragePluginContext(self.etcd, self.local_config)
        await plugin_ctx.init()
        self.storage_plugin_ctx = plugin_ctx
        self.backends = {
            **DEFAULT_BACKENDS,
        }
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            log.info("Loading storage plugin: {0}", plugin_name)
            volume_cls = plugin_instance.get_volume_class()
            self.backends[plugin_name] = volume_cls

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {name: VolumeInfo(**info) for name, info in self.local_config["volume"].items()}

    async def __aexit__(self, *exc_info) -> Optional[bool]:
        await self.storage_plugin_ctx.cleanup()
        return None

    @actxmgr
    async def get_volume(self, name: str) -> AsyncIterator[AbstractVolume]:
        try:
            volume_config = self.local_config["volume"][name]
        except KeyError:
            raise InvalidVolumeError(name)
        volume_cls: Type[AbstractVolume] = self.backends[volume_config["backend"]]
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
