import asyncio
import logging
import os
import signal
import ssl
import subprocess
import sys
from pathlib import Path
from pprint import pformat, pprint

import aiofiles
import aiotools
import click
import trafaret as t
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.common import config, utils
from ai.backend.common import validators as tx
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.logging import BraceStyleAdapter, Logger
from ai.backend.common.types import LogSeverity
from ai.backend.common.utils import Fstab

from . import __version__ as VERSION

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

shutdown_enabled = False


@web.middleware
async def auth_middleware(request, handler):
    token = request.headers.get("X-BackendAI-Watcher-Token", None)
    if token == request.app["token"]:
        try:
            return await handler(request)
        except FileNotFoundError as e:
            log.info(repr(e))
            message = "Agent is not loaded with systemctl."
            return web.json_response({"message": message}, status=200)
        except Exception as e:
            log.exception(repr(e))
            raise
    log.info("invalid requested token")
    return web.HTTPForbidden()


async def handle_status(request: web.Request) -> web.Response:
    svc = request.app["config"]["watcher"]["target-service"]
    proc = await asyncio.create_subprocess_exec(
        *["sudo", "systemctl", "is-active", svc], stdout=subprocess.PIPE
    )
    if proc.stdout is not None:
        status = (await proc.stdout.read()).strip().decode()
    else:
        status = "unknown"
    await proc.wait()
    return web.json_response({
        "agent-status": status,  # maybe also "inactive", "activating"
        "watcher-status": "active",
    })


async def handle_soft_reset(request: web.Request) -> web.Response:
    svc = request.app["config"]["watcher"]["target-service"]
    proc = await asyncio.create_subprocess_exec(*["sudo", "systemctl", "reload", svc])
    await proc.wait()
    return web.json_response({
        "result": "ok",
    })


async def handle_hard_reset(request: web.Request) -> web.Response:
    svc = request.app["config"]["watcher"]["target-service"]
    proc = await asyncio.create_subprocess_exec(*["sudo", "systemctl", "stop", svc])
    await proc.wait()
    proc = await asyncio.create_subprocess_exec(*["sudo", "systemctl", "restart", "docker.service"])
    await proc.wait()
    proc = await asyncio.create_subprocess_exec(*["sudo", "systemctl", "start", svc])
    await proc.wait()
    return web.json_response({
        "result": "ok",
    })


async def handle_shutdown(request: web.Request) -> web.Response:
    global shutdown_enabled
    svc = request.app["config"]["watcher"]["target-service"]
    proc = await asyncio.create_subprocess_exec(*["sudo", "systemctl", "stop", svc])
    await proc.wait()
    shutdown_enabled = True
    signal.alarm(1)
    return web.json_response({
        "result": "ok",
    })


async def handle_agent_start(request: web.Request) -> web.Response:
    svc = request.app["config"]["watcher"]["target-service"]
    proc = await asyncio.create_subprocess_exec(*["sudo", "systemctl", "start", svc])
    await proc.wait()
    return web.json_response({
        "result": "ok",
    })


async def handle_agent_stop(request: web.Request) -> web.Response:
    svc = request.app["config"]["watcher"]["target-service"]
    proc = await asyncio.create_subprocess_exec(*["sudo", "systemctl", "stop", svc])
    await proc.wait()
    return web.json_response({
        "result": "ok",
    })


async def handle_agent_restart(request: web.Request) -> web.Response:
    svc = request.app["config"]["watcher"]["target-service"]
    proc = await asyncio.create_subprocess_exec(*["sudo", "systemctl", "restart", svc])
    await proc.wait()
    return web.json_response({
        "result": "ok",
    })


async def handle_fstab_detail(request: web.Request) -> web.Response:
    log.info("HANDLE_FSTAB_DETAIL")
    params = request.query
    fstab_path = params.get("fstab_path", "/etc/fstab")
    async with aiofiles.open(fstab_path, mode="r") as fp:
        content = await fp.read()
        return web.Response(text=content)


async def handle_list_mounts(request: web.Request) -> web.Response:
    log.info("HANDLE_LIST_MOUNT")
    config = request.app["config_server"]
    mount_prefix = await config.get("volumes/_mount")
    if mount_prefix is None:
        mount_prefix = "/mnt"
    mounts = set()
    for p in Path(mount_prefix).iterdir():
        if p.is_dir() and p.is_mount():
            mounts.add(str(p))
    return web.json_response(sorted(mounts))


async def handle_mount(request: web.Request) -> web.Response:
    log.info("HANDLE_MOUNT")
    params = await request.json()
    config = request.app["config_server"]
    mount_prefix = await config.get("volumes/_mount")
    if mount_prefix is None:
        mount_prefix = "/mnt"
    mountpoint = Path(mount_prefix) / params["name"]
    mountpoint.mkdir(exist_ok=True)
    if params.get("options", None):
        cmd = [
            "sudo",
            "mount",
            "-t",
            params["fs_type"],
            "-o",
            params["options"],
            params["fs_location"],
            str(mountpoint),
        ]
    else:
        cmd = ["sudo", "mount", "-t", params["fs_type"], params["fs_location"], str(mountpoint)]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    raw_out, raw_err = await proc.communicate()
    out = raw_out.decode("utf8")
    err = raw_err.decode("utf8")
    await proc.wait()
    if err:
        log.error("Mount error: " + err)
        return web.Response(text=err, status=500)
    log.info("Mounted " + params["name"] + " on " + mount_prefix)
    if params["edit_fstab"]:
        fstab_path = params["fstab_path"] if params["fstab_path"] else "/etc/fstab"
        # FIXME: Remove ignore if https://github.com/python/typeshed/pull/4650 is released
        async with aiofiles.open(fstab_path, mode="r+") as fp:  # type: ignore
            fstab = Fstab(fp)
            await fstab.add(
                params["fs_location"], str(mountpoint), params["fs_type"], params["options"]
            )
    return web.Response(text=out)


async def handle_umount(request: web.Request) -> web.Response:
    log.info("HANDLE_UMOUNT")
    params = await request.json()
    config = request.app["config_server"]
    mount_prefix = await config.get("volumes/_mount")
    if mount_prefix is None:
        mount_prefix = "/mnt"
    mountpoint = Path(mount_prefix) / params["name"]
    assert Path(mount_prefix) != mountpoint
    proc = await asyncio.create_subprocess_exec(
        *[
            "sudo",
            "umount",
            str(mountpoint),
        ],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    raw_out, raw_err = await proc.communicate()
    out = raw_out.decode("utf8")
    err = raw_err.decode("utf8")
    await proc.wait()
    if err:
        log.error("Unmount error: " + err)
        return web.Response(text=err, status=500)
    log.info("Unmounted " + params["name"] + " from " + mount_prefix)
    try:
        mountpoint.rmdir()  # delete directory if empty
    except OSError:
        pass
    if params["edit_fstab"]:
        fstab_path = params["fstab_path"] if params["fstab_path"] else "/etc/fstab"
        # FIXME: Remove ignore if https://github.com/python/typeshed/pull/4650 is released
        async with aiofiles.open(fstab_path, mode="r+") as fp:  # type: ignore
            fstab = Fstab(fp)
            await fstab.remove_by_mountpoint(str(mountpoint))
    return web.Response(text=out)


async def init_app(app):
    r = app.router.add_route
    r("GET", "/", handle_status)
    if app["config"]["watcher"]["soft-reset-available"]:
        r("POST", "/soft-reset", handle_soft_reset)
    r("POST", "/hard-reset", handle_hard_reset)
    r("POST", "/shutdown", handle_shutdown)
    r("POST", "/agent/start", handle_agent_start)
    r("POST", "/agent/stop", handle_agent_stop)
    r("POST", "/agent/restart", handle_agent_restart)
    r("GET", "/fstab", handle_fstab_detail)
    r("GET", "/mounts", handle_list_mounts)
    r("POST", "/mounts", handle_mount)
    r("DELETE", "/mounts", handle_umount)


async def shutdown_app(app):
    pass


async def prepare_hook(request, response):
    response.headers["Server"] = "BackendAI-AgentWatcher"


@aiotools.server
async def watcher_server(loop, pidx, args):
    global shutdown_enabled

    app = web.Application()
    app["config"] = args[0]

    etcd_credentials = None
    if app["config"]["etcd"]["user"]:
        etcd_credentials = {
            "user": app["config"]["etcd"]["user"],
            "password": app["config"]["etcd"]["password"],
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
    }
    etcd = AsyncEtcd(
        app["config"]["etcd"]["addr"],
        app["config"]["etcd"]["namespace"],
        scope_prefix_map=scope_prefix_map,
        credentials=etcd_credentials,
    )
    app["config_server"] = etcd

    token = await etcd.get("config/watcher/token")
    if token is None:
        token = "insecure"
    log.debug("watcher authentication token: {}", token)
    app["token"] = token

    app.middlewares.append(auth_middleware)
    app.on_shutdown.append(shutdown_app)
    app.on_startup.append(init_app)
    app.on_response_prepare.append(prepare_hook)
    ssl_ctx = None
    if app["config"]["watcher"]["ssl-enabled"]:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            str(app["config"]["watcher"]["ssl-cert"]),
            str(app["config"]["watcher"]["ssl-privkey"]),
        )
    runner = web.AppRunner(app)
    await runner.setup()
    watcher_addr = app["config"]["watcher"]["service-addr"]
    site = web.TCPSite(
        runner,
        str(watcher_addr.host),
        watcher_addr.port,
        backlog=5,
        reuse_port=True,
        ssl_context=ssl_ctx,
    )
    await site.start()
    log.info("started at {}", watcher_addr)
    try:
        stop_sig = yield
    finally:
        log.info("shutting down...")
        if stop_sig == signal.SIGALRM and shutdown_enabled:
            log.warning("shutting down the agent node!")
            subprocess.run(["shutdown", "-h", "now"])
        await runner.cleanup()


@click.command()
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="The config file path. (default: ./agent.conf and /etc/backend.ai/agent.conf)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Set the logging level to DEBUG",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogSeverity], case_sensitive=False),
    default=LogSeverity.INFO,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    config_path: str,
    log_level: LogSeverity,
    debug: bool,
) -> None:
    watcher_config_iv = (
        t.Dict({
            t.Key("watcher"): t.Dict({
                t.Key("service-addr", default=("0.0.0.0", 6009)): tx.HostPortPair,
                t.Key("ssl-enabled", default=False): t.Bool,
                t.Key("ssl-cert", default=None): t.Null | tx.Path(type="file"),
                t.Key("ssl-key", default=None): t.Null | tx.Path(type="file"),
                t.Key("target-service", default="backendai-agent.service"): t.String,
                t.Key("soft-reset-available", default=False): t.Bool,
            }).allow_extra("*"),
            t.Key("logging"): t.Any,  # checked in ai.backend.common.logging
            t.Key("debug"): t.Dict({
                t.Key("enabled", default=False): t.Bool,
            }).allow_extra("*"),
        })
        .merge(config.etcd_config_iv)
        .allow_extra("*")
    )

    raw_cfg, cfg_src_path = config.read_from_file(config_path, "agent")

    config.override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
    config.override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
    config.override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
    config.override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")
    config.override_with_env(
        raw_cfg, ("watcher", "service-addr", "host"), "BACKEND_WATCHER_SERVICE_IP"
    )
    config.override_with_env(
        raw_cfg, ("watcher", "service-addr", "port"), "BACKEND_WATCHER_SERVICE_PORT"
    )
    if debug:
        log_level = LogSeverity.DEBUG
    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogSeverity.DEBUG)
    config.override_key(raw_cfg, ("logging", "level"), log_level)
    config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)

    try:
        cfg = config.check(raw_cfg, watcher_config_iv)
        if "debug" in cfg and cfg["debug"]["enabled"]:
            print("== Watcher configuration ==")
            pprint(cfg)
        cfg["_src"] = cfg_src_path
    except config.ConfigurationError as e:
        print("Validation of watcher configuration has failed:", file=sys.stderr)
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()

    # Change the filename from the logging config's file section.
    log_sockpath = Path(f"/tmp/backend.ai/ipc/watcher-logger-{os.getpid()}.sock")
    log_sockpath.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f"ipc://{log_sockpath}"
    cfg["logging"]["endpoint"] = log_endpoint
    logger = Logger(cfg["logging"], is_master=True, log_endpoint=log_endpoint)
    if "file" in cfg["logging"]["drivers"]:
        fn = Path(cfg["logging"]["file"]["filename"])
        cfg["logging"]["file"]["filename"] = f"{fn.stem}-watcher{fn.suffix}"

    setproctitle(f"backend.ai: watcher {cfg['etcd']['namespace']}")
    with logger:
        log.info("Backend.AI Agent Watcher {0}", VERSION)
        log.info("runtime: {0}", utils.env_info())

        log_config = logging.getLogger("ai.backend.agent.config")
        log_config.debug("debug mode enabled.")

        aiotools.start_server(
            watcher_server,
            num_workers=1,
            args=(cfg,),
            stop_signals={signal.SIGINT, signal.SIGTERM, signal.SIGALRM},
        )
        log.info("exit.")


if __name__ == "__main__":
    main()
