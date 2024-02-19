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

import aiohttp_cors
from aiohttp import web

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.logging import BraceStyleAdapter

from .abc import AbstractVolume
from .api.client import init_client_app
from .api.manager import init_manager_app
from .api.types import WebMiddleware
from .cephfs import CephFSVolume
from .ddn import EXAScalerFSVolume
from .dellemc import DellEMCOneFSVolume
from .exception import InvalidVolumeError
from .gpfs import GPFSVolume
from .netapp import NetAppVolume
from .plugin import (
    BasePluginContext,
    StorageClientWebappPluginContext,
    StorageManagerWebappPluginContext,
    StoragePluginContext,
)
from .purestorage import FlashBladeVolume
from .types import VolumeInfo
from .vast import VASTVolume
from .vfs import BaseVolume
from .watcher import WatcherClient
from .weka import WekaVolume
from .xfs import XfsVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "storage-proxy"

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


async def on_prepare(request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


def _init_subapp(
    pkg_name: str,
    root_app: web.Application,
    subapp: web.Application,
    global_middlewares: list[WebMiddleware],
) -> None:
    subapp.on_response_prepare.append(on_prepare)

    async def _set_root_ctx(subapp: web.Application):
        # Allow subapp's access to the root app properties.
        # These are the public APIs exposed to plugins as well.
        subapp["ctx"] = root_app["ctx"]

    # We must copy the public interface prior to all user-defined startup signal handlers.
    subapp.on_startup.insert(0, _set_root_ctx)
    if "prefix" not in subapp:
        subapp["prefix"] = pkg_name.split(".")[-1].replace("_", "-")
    prefix = subapp["prefix"]
    root_app.add_subapp("/" + prefix, subapp)
    root_app.middlewares.extend(global_middlewares)


class RootContext:
    pid: int
    etcd: AsyncEtcd
    local_config: Mapping[str, Any]
    dsn: str | None
    event_producer: EventProducer
    event_dispatcher: EventDispatcher
    watcher: WatcherClient | None

    def __init__(
        self,
        pid: int,
        pidx: int,
        node_id: str,
        local_config: Mapping[str, Any],
        etcd: AsyncEtcd,
        *,
        event_producer: EventProducer,
        event_dispatcher: EventDispatcher,
        watcher: WatcherClient | None,
        dsn: Optional[str] = None,
    ) -> None:
        self.pid = pid
        self.pidx = pidx
        self.node_id = node_id
        self.etcd = etcd
        self.local_config = local_config
        self.dsn = dsn
        self.event_producer = event_producer
        self.event_dispatcher = event_dispatcher
        self.watcher = watcher
        self.cors_options = {
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=False, expose_headers="*", allow_headers="*"
            ),
        }

    async def __aenter__(self) -> None:
        self.client_api_app = await init_client_app(self)
        self.manager_api_app = await init_manager_app(self)
        self.backends = {
            **DEFAULT_BACKENDS,
        }
        await self.init_storage_plugin()
        self.manager_webapp_plugin_ctx = await self.init_storage_webapp_plugin(
            StorageManagerWebappPluginContext(self.etcd, self.local_config),
            self.manager_api_app,
        )
        self.client_webapp_plugin_ctx = await self.init_storage_webapp_plugin(
            StorageClientWebappPluginContext(self.etcd, self.local_config),
            self.client_api_app,
        )

    async def init_storage_plugin(self) -> None:
        plugin_ctx = StoragePluginContext(self.etcd, self.local_config)
        await plugin_ctx.init()
        self.storage_plugin_ctx = plugin_ctx
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            log.info("Loading storage plugin: {0}", plugin_name)
            volume_cls = plugin_instance.get_volume_class()
            self.backends[plugin_name] = volume_cls

    async def init_storage_webapp_plugin(
        self, plugin_ctx: BasePluginContext, root_app: web.Application
    ) -> BasePluginContext:
        await plugin_ctx.init()
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            if self.pid == 0:
                log.info("Loading storage webapp plugin: {0}", plugin_name)
            subapp, global_middlewares = await plugin_instance.create_app(self.cors_options)
            _init_subapp(plugin_name, root_app, subapp, global_middlewares)
        return plugin_ctx

    def list_volumes(self) -> Mapping[str, VolumeInfo]:
        return {name: VolumeInfo(**info) for name, info in self.local_config["volume"].items()}

    async def __aexit__(self, *exc_info) -> Optional[bool]:
        await self.storage_plugin_ctx.cleanup()
        await self.manager_webapp_plugin_ctx.cleanup()
        await self.client_webapp_plugin_ctx.cleanup()
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
            event_dispathcer=self.event_dispatcher,
            event_producer=self.event_producer,
        )
        await volume_obj.init()
        try:
            yield volume_obj
        finally:
            await volume_obj.shutdown()
