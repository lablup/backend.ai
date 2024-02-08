import asyncio
import logging
import os
import signal
import ssl
import sys
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from pprint import pformat, pprint
from typing import TYPE_CHECKING, Any, AsyncIterator

import aiohttp_cors
import aiotools
import click
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.common import config
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.logging import BraceStyleAdapter, Logger
from ai.backend.common.types import LogSeverity
from ai.backend.common.utils import env_info

from . import __version__ as VERSION
from .api import AUTH_PASS, auth_middleware
from .config import watcher_config_iv
from .context import RootContext
from .defs import CORSOptions, WebMiddleware
from .plugin import WatcherPluginContext, WatcherWebAppPluginContext

if TYPE_CHECKING:
    from ai.backend.common.types import HostPortPair


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


async def ping(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "version": VERSION,
        },
        status=200,
    )


async def get_plugins(request: web.Request) -> web.Response:
    ctx: RootContext = request.app["ctx"]

    if ctx.webapp_ctx is None:
        return web.Response(status=503, text="Plugins are not initialized")

    app_list = [
        {
            "plugin": plugin_name,
            "plugin_group": ctx.webapp_ctx.plugin_group,
            "route_prefix": plugin.route_prefix,
            "plugin_path": plugin.app_path,
            "publicity": plugin.is_public,
        }
        for plugin_name, plugin in ctx.webapp_ctx.plugins.items()
    ]
    if not request.get(AUTH_PASS, False):
        app_list = [info for info in app_list if info["publicity"]]
    return web.json_response(
        app_list,
        status=200,
    )


def init_subapp(
    pkg_name: str,
    root_app: web.Application,
    subapp: web.Application,
    global_middlewares: list[WebMiddleware],
) -> None:
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


async def _init_subapp(
    root_app: web.Application,
    root_ctx: RootContext,
    etcd: AsyncEtcd,
    local_config: dict[str, Any],
    cors_options: CORSOptions,
) -> WatcherWebAppPluginContext:
    webapp_plugin_ctx = WatcherWebAppPluginContext(etcd, local_config)
    await webapp_plugin_ctx.init(
        root_ctx,
        allowlist=local_config["watcher"]["allowed-plugins"],
        blocklist=local_config["watcher"]["disabled-plugins"],
    )
    for plugin_name, plugin_instance in webapp_plugin_ctx.plugins.items():
        log.info(f"Loading webapp plugin: {plugin_name}")
        subapp, global_middlewares = await plugin_instance.create_app(cors_options)
        init_subapp(plugin_name, root_app, subapp, global_middlewares)

    return webapp_plugin_ctx


async def _init_watcher(
    ctx: RootContext,
    etcd: AsyncEtcd,
    local_config: dict[str, Any],
) -> WatcherPluginContext:
    watcher_ctx = WatcherPluginContext(etcd, local_config)
    module_config: dict[str, Any] = local_config["module"]
    await watcher_ctx.init()
    for _, plugin_instance in watcher_ctx.plugins.items():
        watcher_cls, watcher_config_cls = plugin_instance.get_watcher_class()
        watcher_name = str(watcher_cls.name)
        try:
            plugin_config = module_config[watcher_name]
        except KeyError:
            log.warning(f"Config not found. Skip initiating watcher. (name: {watcher_name})")
            continue
        log.info("Loading watcher plugin: {0}", watcher_name)
        watcher = watcher_cls(ctx, watcher_config_cls, plugin_config)
        ctx.register_watcher(watcher)
    return watcher_ctx


@aiotools.server_context
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: list[Any],
) -> AsyncIterator[None]:
    try:
        asyncio.get_child_watcher()
    except (AttributeError, NotImplementedError):
        pass
    log_endpoint = _args[1]
    logger = Logger(_args[0]["logging"], is_master=False, log_endpoint=log_endpoint)
    with logger:
        async with server_main(loop, pidx, _args):
            yield


@actxmgr
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    args: list[Any],
) -> AsyncIterator[None]:
    app = web.Application()
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }
    local_config = args[0]

    etcd_credentials = None
    if local_config["etcd"]["user"]:
        etcd_credentials = {
            "user": local_config["etcd"]["user"],
            "password": local_config["etcd"]["password"],
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
    }
    etcd = AsyncEtcd(
        local_config["etcd"]["addr"],
        local_config["etcd"]["namespace"],
        scope_prefix_map=scope_prefix_map,
        credentials=etcd_credentials,
    )
    app["config_server"] = etcd

    # Set token
    token = await etcd.get("config/watcher/token")
    if token is None:
        token = "insecure"
    log.debug("watcher authentication token: {}", token)
    app["token"] = token

    ssl_ctx = None
    if local_config["watcher"]["ssl-enabled"]:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            str(local_config["watcher"]["ssl-cert"]),
            str(local_config["watcher"]["ssl-privkey"]),
        )
    ctx = RootContext(
        pid=os.getpid(),
        node_id=local_config["watcher"]["node-id"],
        pidx=pidx,
        local_config=local_config,
        etcd=etcd,
    )
    app["ctx"] = ctx
    app.middlewares.append(auth_middleware)
    cors = aiohttp_cors.setup(app, defaults=cors_options)
    cors.add(app.router.add_route("GET", r"", ping))
    cors.add(app.router.add_route("GET", r"/", ping))
    cors.add(app.router.add_route("GET", "/plugins", get_plugins))

    watcher_ctx = await _init_watcher(ctx, etcd, local_config)
    webapp_plugin_ctx = await _init_subapp(app, ctx, etcd, local_config, cors_options)
    ctx.webapp_ctx = webapp_plugin_ctx

    runner = web.AppRunner(app)
    await runner.setup()
    watcher_addr: HostPortPair = local_config["watcher"]["service-addr"]
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
        if stop_sig == signal.SIGALRM:
            log.warning(f"Stop signal: {stop_sig}")
        await webapp_plugin_ctx.cleanup()
        await watcher_ctx.cleanup()
        await runner.cleanup()


@click.command()
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help=(
        "The config file path. "
        "[default: searching watcher.toml in ./, ~/.config/backend.ai/, and /etc/backend.ai/]"
    ),
)
@click.option(
    "--debug",
    is_flag=True,
    help=(
        "Alias of `--log-level debug`. It will override `--log-level` value to `debug` if this"
        " option is set."
    ),
)
@click.option(
    "--log-level",
    type=click.Choice([*LogSeverity.__members__.keys()], case_sensitive=False),
    default=LogSeverity.INFO,
    help="Choose logging level from... debug, info, warning, error, critical",
)
@click.pass_context
def main(cli_ctx: click.Context, config_path: Path, log_level: LogSeverity, debug: bool = False):
    """Start the watcher service as a foreground process."""
    try:
        raw_cfg, cfg_src_path = config.read_from_file(config_path, "watcher")
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
        if log_level != LogSeverity.DEBUG:
            if (uid := os.geteuid()) != 0:
                raise RuntimeError(f"Watcher must be run as root, not {uid}. Abort.")
        config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogSeverity.DEBUG)
        config.override_key(raw_cfg, ("logging", "level"), log_level.upper())
        config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level.upper())
        config.override_key(raw_cfg, ("logging", "pkg-ns", "aiohttp"), log_level.upper())
        cfg = config.check(raw_cfg, watcher_config_iv)
        if "debug" in cfg and cfg["debug"]["enabled"]:
            print("== Watcher configuration ==")
            pprint(cfg)
        cfg["_src"] = cfg_src_path
    except config.ConfigurationError as e:
        print(
            "ConfigurationError: Could not read or validate the watcher local config:",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()

    if cli_ctx.invoked_subcommand is None:
        pid_file: Path = cfg["watcher"]["pid-file"]
        pid_file.write_text(str(os.getpid()))
        ipc_base_path = cfg["watcher"]["ipc-base-path"]
        log_sockpath = Path(
            ipc_base_path / f"watcher-logger-{os.getpid()}.sock",
        )
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        cfg["logging"]["endpoint"] = log_endpoint

        try:
            logger = Logger(
                cfg["logging"],
                is_master=True,
                log_endpoint=log_endpoint,
            )
            with logger:
                setproctitle("backend.ai: watcher")
                log.info("Backend.AI Watcher", VERSION)
                log.info("Runtime: {0}", env_info())
                log.info("Node ID: {0}", cfg["watcher"]["node-id"])
                log_config = logging.getLogger("ai.backend.watcher.config")
                if cfg["debug"]["enabled"]:
                    log_config.debug("debug mode enabled.")
                if "debug" in cfg and cfg["debug"]["enabled"]:
                    print("== Watcher configuration ==")
                    pprint(cfg)
                if cfg["watcher"]["event-loop"] == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                aiotools.start_server(
                    server_main_logwrapper,
                    num_workers=1,
                    args=(cfg, log_endpoint),
                    stop_signals={signal.SIGINT, signal.SIGTERM, signal.SIGALRM},
                )
                log.info("exit.")
        finally:
            if pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                pid_file.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
