from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, Final, Mapping

import aiohttp_cors
import aiotools
import attrs
import trafaret as t
from aiohttp import web

from ai.backend.common.bgtask import BackgroundTaskManager
from ai.backend.common.config import redis_config_iv
from ai.backend.common.defs import MOUNT_MAP_KEY, REDIS_STREAM_DB
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import (
    DoVolumeMountEvent,
    DoVolumeUnmountEvent,
    EventDispatcher,
    EventProducer,
    VolumeMounted,
    VolumeUnmounted,
)
from ai.backend.common.types import AgentId, VolumeMountableNodeType
from ai.backend.watcher.base import MountErrorHandler as AbcMountErrorHandler
from ai.backend.watcher.context import RootContext
from ai.backend.watcher.defs import CORSOptions, WebMiddleware
from ai.backend.watcher.plugin import AbstractWatcherWebAppPlugin

from .watcher import StorageWatcher

if TYPE_CHECKING:
    from ai.backend.common.bgtask import ProgressReporter

STORAGE_WATCHER: Final = StorageWatcher.name


async def ping(request: web.Request) -> web.Response:
    ctx: RootContext = request.app["ctx"]
    return web.Response(status=200, body=f"Storage watcher webapp alive. (node id: {ctx.node_id})")


async def handle_get_mount(request: web.Request) -> web.Response:
    mount_path = request.match_info["mount_path"]
    return web.json_response({
        "mount_path": mount_path,
        "is_mounted": Path(mount_path).is_mount(),
    })


async def rmdir(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    watcher = app_ctx.watcher
    path = Path(request.match_info["dirpath"])

    body_scheme = t.Dict(
        {
            t.Key("force", default=False): t.ToBool(),
        },
    )
    raw_params = await request.json()
    data: dict[str, Any] = body_scheme.check(raw_params)
    option = "-rf" if data["force"] else "-r"

    async def _rmdir(reporter: ProgressReporter) -> None:
        async def task() -> None:
            for subdir in path.iterdir():
                result = await watcher.run_cmd(["sudo", "rm", option, str(subdir)])
                progress_msg = "" if result.succeeded else result.body
                await reporter.update(1, message=progress_msg)

        async with aiotools.TaskGroup() as tg:
            tg.create_task(task())

    task_id = await app_ctx.background_task_manager.start(_rmdir)
    return web.json_response({"task_id": str(task_id)})


@attrs.define(slots=True)
class PrivateContext:
    watcher: StorageWatcher
    node_id: str
    ptask_group: aiotools.PersistentTaskGroup
    etcd: AsyncEtcd
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    background_task_manager: BackgroundTaskManager


async def _webapp_init(app: web.Application):
    pass


async def _webapp_shutdown(app: web.Application):
    pass


async def _app_ctx(app: web.Application) -> AsyncIterator[None]:
    yield


class StorageWatcherWebapp(AbstractWatcherWebAppPlugin):
    app_path = "ai.backend.watcher_modules.storage.webapp"
    route_prefix = "storage-watcher"
    watcher: StorageWatcher
    ptask_group: aiotools.PersistentTaskGroup
    event_dispatcher: EventDispatcher
    event_producer: EventProducer

    async def init(self, context: Any = None) -> None:
        assert isinstance(context, RootContext)
        self.root_ctx = context
        _watcher = self.root_ctx.get_watcher(STORAGE_WATCHER)
        assert isinstance(_watcher, StorageWatcher)
        self.watcher = _watcher
        self.ptask_group = aiotools.PersistentTaskGroup(name="storage_watcher_taskgroup")
        await self.watcher.init()
        redis_config = redis_config_iv.check(
            await context.etcd.get_prefix("config/redis"),
        )
        _config = self.watcher.config
        if _config.event["connect_server"]:
            if (consumer_group := _config.event["consumer_group"]) is None:
                raise RuntimeError("Should set valid `consumer_group` in local config file.")
        self.event_producer = await EventProducer.new(
            redis_config,
            db=REDIS_STREAM_DB,
            log_events=context.local_config["debug"]["log-events"],
        )
        self.event_dispatcher = await EventDispatcher.new(
            redis_config,
            db=REDIS_STREAM_DB,
            log_events=context.local_config["debug"]["log-events"],
            node_id=context.node_id,
            consumer_group=consumer_group,
        )

    async def cleanup(self) -> None:
        await self.ptask_group.shutdown()
        await self.watcher.shutdown()

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = new_plugin_config

    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, list[WebMiddleware]]:
        app = web.Application()
        app["prefix"] = self.route_prefix
        private_ctx = PrivateContext(
            watcher=self.watcher,
            node_id=self.root_ctx.node_id,
            ptask_group=self.ptask_group,
            etcd=self.root_ctx.etcd,
            event_dispatcher=self.event_dispatcher,
            event_producer=self.event_producer,
            background_task_manager=BackgroundTaskManager(self.event_producer),
        )
        app["agent-watcher.context"] = private_ctx
        app.on_startup.append(_webapp_init)
        app.on_shutdown.append(_webapp_shutdown)
        app.cleanup_ctx.append(_app_ctx)
        cors = aiohttp_cors.setup(app, defaults=cors_options)
        cors.add(app.router.add_route("GET", "/ping", ping))
        cors.add(app.router.add_route("GET", "/mounts/{mount_path}", handle_get_mount))
        cors.add(app.router.add_route("DELETE", "/{dirpath}", rmdir))

        evd = private_ctx.event_dispatcher
        evd.subscribe(
            DoVolumeMountEvent,
            private_ctx,
            handle_volume_mount,
            name="storage.volume.mount",
        )
        evd.subscribe(
            DoVolumeUnmountEvent,
            private_ctx,
            handle_volume_umount,
            name="storage.volume.umount",
        )
        if self.watcher.config.poll_directory_mount:
            mount_map = await self.root_ctx.etcd.get_prefix(MOUNT_MAP_KEY)
            mount_paths = [p for p in mount_map.keys()]
            self.ptask_group.create_task(
                self.watcher.poll_directory_mount(
                    mount_paths,
                    error_handler=MountErrorHandler(private_ctx),
                    return_when_error=False,
                )
            )
        return app, []


async def handle_volume_mount(
    context: PrivateContext,
    source: AgentId,
    event: DoVolumeMountEvent,
) -> None:
    watcher = context.watcher
    mount_path = Path(event.dir_name)
    if watcher.config.ignore_mount_event:
        await context.event_producer.produce_event(
            VolumeMounted(
                "mount-skipped",
                str(context.node_id),
                VolumeMountableNodeType.STORAGE_PROXY,
                str(mount_path),
            )
        )
        return
    mounted = await watcher.mount(
        str(mount_path),
        event.fs_location,
        event.fs_type,
        event.cmd_options,
        event.edit_fstab,
        event.fstab_path,
    )

    if mounted:
        await watcher.chown(mount_path, watcher.config.bai_uid, watcher.config.bai_gid)
        await context.etcd.put(f"{MOUNT_MAP_KEY}/{str(mount_path)}", event.fs_location)
        reason = "mount-success"
    else:
        reason = "already-mounted"
    await context.event_producer.produce_event(
        VolumeMounted(
            reason,
            str(context.node_id),
            VolumeMountableNodeType.STORAGE_PROXY,
            str(mount_path),
        )
    )


async def handle_volume_umount(
    context: PrivateContext,
    source: AgentId,
    event: DoVolumeUnmountEvent,
) -> None:
    watcher = context.watcher
    mount_path = Path(event.dir_name)
    if watcher.config.ignore_mount_event:
        await context.event_producer.produce_event(
            VolumeMounted(
                "mount-skipped",
                str(context.node_id),
                VolumeMountableNodeType.STORAGE_PROXY,
                str(mount_path),
            )
        )
        return
    timeout = await context.etcd.get("config/watcher/file-io-timeout")
    umounted = await watcher.umount(
        str(mount_path),
        event.edit_fstab,
        event.fstab_path,
        timeout_sec=float(timeout) if timeout is not None else None,
    )
    if umounted:
        await context.etcd.delete(f"{MOUNT_MAP_KEY}/{str(mount_path)}")
        reason = "umount-success"
    else:
        reason = "already-umounted"
    await context.event_producer.produce_event(
        VolumeUnmounted(
            reason,
            str(context.node_id),
            VolumeMountableNodeType.STORAGE_PROXY,
            str(mount_path),
        )
    )


class MountErrorHandler(AbcMountErrorHandler):
    def __init__(self, ctx: PrivateContext) -> None:
        self.ctx = ctx

    async def call(self, path: str, reason: str) -> None:
        await self.ctx.event_producer.produce_event(
            VolumeUnmounted(
                "mount-fail",
                str(self.ctx.node_id),
                VolumeMountableNodeType.STORAGE_PROXY,
                path,
                err_msg=reason,
            )
        )
