from __future__ import annotations

import json
import logging
import signal
from pathlib import Path
from typing import Any, AsyncIterator, Final, Mapping

import aiofiles
import aiohttp_cors
import aiotools
import attrs
import trafaret as t
from aiohttp import web

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
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AgentId, VolumeMountableNodeType
from ai.backend.watcher.api import auth_required
from ai.backend.watcher.base import MountErrorHandler as AbcMountErrorHandler
from ai.backend.watcher.context import RootContext
from ai.backend.watcher.defs import CORSOptions, WebMiddleware
from ai.backend.watcher.plugin import AbstractWatcherWebAppPlugin

from .watcher import AgentWatcher

log = BraceStyleAdapter(logging.getLogger(__name__))


AGENT_WATCHER: Final = AgentWatcher.name


async def _mount(
    context: PrivateContext,
    mount_path: Path,
    fs_location: str,
    fs_type: str,
    cmd_options: str | None = None,
    edit_fstab: bool = False,
    fstab_path: str | None = None,
) -> bool:
    mounted = await context.watcher.mount(
        str(mount_path),
        fs_location,
        fs_type,
        cmd_options,
        edit_fstab,
        fstab_path,
    )
    if mounted:
        await context.etcd.put(f"{MOUNT_MAP_KEY}/{str(mount_path)}", fs_location)
    return mounted


async def _umount(
    context: PrivateContext,
    mount_path: Path,
    edit_fstab: bool = False,
    fstab_path: str | None = None,
) -> bool:
    timeout = await context.etcd.get("config/watcher/file-io-timeout")
    umounted = await context.watcher.umount(
        str(mount_path),
        edit_fstab,
        fstab_path,
        timeout_sec=float(timeout) if timeout is not None else None,
    )
    if umounted:
        await context.etcd.delete(f"{MOUNT_MAP_KEY}/{str(mount_path)}")
    return umounted


async def ping(request: web.Request) -> web.Response:
    return web.Response(status=200, body="Agent watcher webapp alive.")


@auth_required
async def mount(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    log.info("AGENT_WATCHER.MOUNT")

    body_scheme = t.Dict(
        {
            t.Key("name"): t.String(allow_blank=True),
            t.Key("fs_location"): t.String(),
            t.Key("fs_type"): t.String(),
            t.Key("options", default=None): t.Null | t.String(),
            t.Key("edit_fstab", default=False): t.String(),
            t.Key("fstab_path", default="/etc/fstab"): t.String(),
        },
    )
    try:
        raw_params = await request.json()
        data: dict[str, Any] = body_scheme.check(raw_params)
    except (json.decoder.JSONDecodeError, t.DataError):
        return web.Response(text="Invalid data", status=400)
    mount_path = Path(data["name"])
    await _mount(
        app_ctx,
        mount_path,
        data["fs_location"],
        data["fs_type"],
        data["options"],
        data["edit_fstab"],
        data["fstab_path"],
    )
    return web.Response(status=201)


@auth_required
async def umount(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    log.info("AGENT_WATCHER.UMOUNT")

    body_scheme = t.Dict(
        {
            t.Key("name"): t.String(allow_blank=True),
            t.Key("edit_fstab", default=False): t.String(),
            t.Key("fstab_path", default="/etc/fstab"): t.String(),
        },
    )
    try:
        raw_params = await request.json()
        data: dict[str, Any] = body_scheme.check(raw_params)
    except (json.decoder.JSONDecodeError, t.DataError):
        return web.Response(text="Invalid data", status=400)
    mount_path = Path(data["name"])
    await _umount(
        app_ctx,
        mount_path,
        data["edit_fstab"],
        data["fstab_path"],
    )
    return web.Response(status=201)


async def handle_status(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    watcher = app_ctx.watcher
    result = await watcher.run_cmd(["sudo", "systemctl", "is-active", watcher.config.service_name])
    status = result.body if result.succeeded else "unknown"
    return web.json_response({
        "agent-status": status,  # maybe also "inactive", "activating"
        "watcher-status": "active",
    })


async def handle_soft_reset(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    watcher = app_ctx.watcher
    await watcher.run_cmd(["sudo", "systemctl", "reload", watcher.config.service_name])
    return web.json_response({
        "result": "ok",
    })


async def handle_hard_reset(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    watcher = app_ctx.watcher
    await watcher.run_cmd(["sudo", "systemctl", "stop", watcher.config.service_name])
    await watcher.run_cmd(["sudo", "systemctl", "restart", "docker.service"])
    await watcher.run_cmd(["sudo", "systemctl", "start", watcher.config.service_name])
    return web.json_response({
        "result": "ok",
    })


async def handle_shutdown(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    watcher = app_ctx.watcher
    await watcher.run_cmd(["sudo", "systemctl", "stop", watcher.config.service_name])
    signal.alarm(1)
    return web.json_response({
        "result": "ok",
    })


async def handle_agent_start(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    watcher = app_ctx.watcher
    await watcher.run_cmd(["sudo", "systemctl", "start", watcher.config.service_name])
    return web.json_response({
        "result": "ok",
    })


async def handle_agent_stop(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    watcher = app_ctx.watcher
    await watcher.run_cmd(["sudo", "systemctl", "stop", watcher.config.service_name])
    return web.json_response({
        "result": "ok",
    })


async def handle_agent_restart(request: web.Request) -> web.Response:
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    watcher = app_ctx.watcher
    await watcher.run_cmd(["sudo", "systemctl", "restart", watcher.config.service_name])
    return web.json_response({
        "result": "ok",
    })


async def handle_fstab_detail(request: web.Request) -> web.Response:
    log.info("HANDLE_FSTAB_DETAIL")
    fstab_path = request.query.get("fstab_path", "/etc/fstab")
    async with aiofiles.open(fstab_path, mode="r") as fp:
        content = await fp.read()
    return web.Response(text=content)


async def handle_list_mounts(request: web.Request) -> web.Response:
    log.info("HANDLE_LIST_MOUNT")
    root_ctx: RootContext = request.app["ctx"]
    mount_map = await root_ctx.etcd.get_prefix(MOUNT_MAP_KEY)
    mounts = set()
    for path in mount_map.keys():
        if Path(path).is_mount():
            mounts.add(path)
    return web.json_response(sorted(mounts))


async def handle_get_mount(request: web.Request) -> web.Response:
    log.info("HANDLE_GET_MOUNT")
    app_ctx: PrivateContext = request.app["agent-watcher.context"]
    mount_map = await app_ctx.etcd.get_prefix(MOUNT_MAP_KEY)
    mount_paths = [p for p in mount_map.keys()]
    mount_path = request.match_info["mount_path"]
    if mount_path not in mount_paths:
        return web.Response(status=404)
    return web.json_response({
        "mount_prefix": "",
        "mount_path": mount_path,
        "is_mounted": Path(mount_path).is_mount(),
    })


@attrs.define(slots=True)
class PrivateContext:
    watcher: AgentWatcher
    node_id: str
    ptask_group: aiotools.PersistentTaskGroup
    etcd: AsyncEtcd
    event_dispatcher: EventDispatcher
    event_producer: EventProducer


async def _webapp_init(app: web.Application):
    pass


async def _webapp_shutdown(app: web.Application):
    pass


async def _app_ctx(app: web.Application) -> AsyncIterator[None]:
    yield


class AgentWatcherWebapp(AbstractWatcherWebAppPlugin):
    app_path = "ai.backend.watcher_modules.agent.webapp"
    route_prefix = "agent-watcher"
    watcher: AgentWatcher
    ptask_group: aiotools.PersistentTaskGroup
    event_dispatcher: EventDispatcher
    event_producer: EventProducer

    async def init(self, context: Any = None) -> None:
        assert isinstance(context, RootContext)
        self.root_ctx = context
        _watcher = self.root_ctx.get_watcher(AGENT_WATCHER)
        assert isinstance(_watcher, AgentWatcher)
        self.watcher = _watcher
        self.ptask_group = aiotools.PersistentTaskGroup(name="agent_watcher_taskgroup")
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
        )
        app["agent-watcher.context"] = private_ctx
        app.on_startup.append(_webapp_init)
        app.on_shutdown.append(_webapp_shutdown)
        app.cleanup_ctx.append(_app_ctx)
        cors = aiohttp_cors.setup(app, defaults=cors_options)
        cors.add(app.router.add_route("GET", "/", handle_status))
        cors.add(app.router.add_route("GET", "/status", handle_status))
        cors.add(app.router.add_route("GET", "/ping", ping))
        if self.watcher.config.soft_reset_available:
            cors.add(app.router.add_route("POST", "/soft-reset", handle_soft_reset))
        cors.add(app.router.add_route("POST", "/hard-reset", handle_hard_reset))
        cors.add(app.router.add_route("POST", "/shutdown", handle_shutdown))
        cors.add(app.router.add_route("POST", "/agent/start", handle_agent_start))
        cors.add(app.router.add_route("POST", "/agent/stop", handle_agent_stop))
        cors.add(app.router.add_route("POST", "/agent/restart", handle_agent_restart))
        cors.add(app.router.add_route("GET", "/fstab", handle_fstab_detail))
        cors.add(app.router.add_route("GET", "/mounts", handle_list_mounts))
        cors.add(app.router.add_route("GET", "/mounts/{mount_path}", handle_get_mount))
        cors.add(app.router.add_route("POST", "/mounts", mount))
        cors.add(app.router.add_route("DELETE", "/mounts", umount))

        evd = private_ctx.event_dispatcher
        evd.subscribe(
            DoVolumeMountEvent,
            private_ctx,
            handle_volume_mount,
            name="ag.volume.mount",
        )
        evd.subscribe(
            DoVolumeUnmountEvent,
            private_ctx,
            handle_volume_umount,
            name="ag.volume.umount",
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
    mount_path = Path(event.dir_name)
    if context.watcher.config.ignore_mount_event:
        await context.event_producer.produce_event(
            VolumeMounted(
                "mount-skipped",
                str(context.node_id),
                VolumeMountableNodeType.AGENT,
                str(mount_path),
            )
        )
        return
    mounted = await _mount(
        context,
        mount_path,
        event.fs_location,
        event.fs_type,
        event.cmd_options,
        event.edit_fstab,
        event.fstab_path,
    )
    reason = "mount-success" if mounted else "already-mounted"
    await context.event_producer.produce_event(
        VolumeMounted(
            reason,
            str(context.node_id),
            VolumeMountableNodeType.AGENT,
            str(mount_path),
        )
    )


async def handle_volume_umount(
    context: PrivateContext,
    source: AgentId,
    event: DoVolumeUnmountEvent,
) -> None:
    mount_path = Path(event.dir_name)
    if context.watcher.config.ignore_mount_event:
        await context.event_producer.produce_event(
            VolumeMounted(
                "mount-skipped",
                str(context.node_id),
                VolumeMountableNodeType.AGENT,
                str(mount_path),
            )
        )
        return
    umounted = await _umount(
        context,
        mount_path,
        event.edit_fstab,
        event.fstab_path,
    )
    reason = "umount-success" if umounted else "already-umounted"
    await context.event_producer.produce_event(
        VolumeUnmounted(
            reason,
            str(context.node_id),
            VolumeMountableNodeType.AGENT,
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
                VolumeMountableNodeType.AGENT,
                path,
                err_msg=reason,
            )
        )
