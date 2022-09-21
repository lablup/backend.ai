import asyncio
import grp
import logging
import multiprocessing
import os
import pwd
import ssl
import sys
from contextlib import closing
from pathlib import Path
from pprint import pformat, pprint
from typing import Any, AsyncIterator, Sequence

import aiomonitor
import aiotools
import click
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.common import config
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.logging import BraceStyleAdapter, Logger
from ai.backend.common.utils import env_info

from . import __version__ as VERSION
from .api.client import init_client_app
from .api.manager import init_manager_app
from .config import local_config_iv
from .context import Context

log = BraceStyleAdapter(logging.getLogger("ai.backend.storage.server"))


@aiotools.server
async def server_main_logwrapper(loop, pidx, _args):
    setproctitle(f"backend.ai: storage-proxy worker-{pidx}")
    try:
        asyncio.get_child_watcher()
    except (AttributeError, NotImplementedError):
        pass
    log_endpoint = _args[1]
    logger = Logger(_args[0]["logging"], is_master=False, log_endpoint=log_endpoint)
    with logger:
        async with server_main(loop, pidx, _args):
            yield


@aiotools.server
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncIterator[None]:
    local_config = _args[0]
    loop.set_debug(local_config["debug"]["asyncio"])
    m = aiomonitor.Monitor(
        loop,
        port=local_config["storage-proxy"]["aiomonitor-port"] + pidx,
        console_enabled=False,
        hook_task_factory=local_config["debug"]["enhanced-aiomonitor-task-info"],
    )
    m.prompt = f"monitor (storage-proxy[{pidx}@{os.getpid()}]) >>> "
    m.start()

    with closing(m):
        etcd_credentials = None
        if local_config["etcd"]["user"]:
            etcd_credentials = {
                "user": local_config["etcd"]["user"],
                "password": local_config["etcd"]["password"],
            }
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
            ConfigScopes.NODE: f"nodes/storage/{local_config['storage-proxy']['node-id']}",
        }
        etcd = AsyncEtcd(
            local_config["etcd"]["addr"],
            local_config["etcd"]["namespace"],
            scope_prefix_map,
            credentials=etcd_credentials,
        )
        ctx = Context(pid=os.getpid(), local_config=local_config, etcd=etcd)
        client_api_app = await init_client_app(ctx)
        manager_api_app = await init_manager_app(ctx)

        client_ssl_ctx = None
        manager_ssl_ctx = None
        if local_config["api"]["client"]["ssl-enabled"]:
            client_ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            client_ssl_ctx.load_cert_chain(
                str(local_config["api"]["client"]["ssl-cert"]),
                str(local_config["api"]["client"]["ssl-privkey"]),
            )
        if local_config["api"]["manager"]["ssl-enabled"]:
            manager_ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            manager_ssl_ctx.load_cert_chain(
                str(local_config["api"]["manager"]["ssl-cert"]),
                str(local_config["api"]["manager"]["ssl-privkey"]),
            )
        client_api_runner = web.AppRunner(client_api_app)
        manager_api_runner = web.AppRunner(manager_api_app)
        await client_api_runner.setup()
        await manager_api_runner.setup()
        client_service_addr = local_config["api"]["client"]["service-addr"]
        manager_service_addr = local_config["api"]["manager"]["service-addr"]
        client_api_site = web.TCPSite(
            client_api_runner,
            str(client_service_addr.host),
            client_service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=client_ssl_ctx,
        )
        manager_api_site = web.TCPSite(
            manager_api_runner,
            str(manager_service_addr.host),
            manager_service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=manager_ssl_ctx,
        )
        await client_api_site.start()
        await manager_api_site.start()
        if os.geteuid() == 0:
            uid = local_config["storage-proxy"]["user"]
            gid = local_config["storage-proxy"]["group"]
            os.setgroups(
                [g.gr_gid for g in grp.getgrall() if pwd.getpwuid(uid).pw_name in g.gr_mem],
            )
            os.setgid(gid)
            os.setuid(uid)
            log.info("Changed process uid:gid to {}:{}", uid, gid)
        log.info("Started service.")
        try:
            yield
        finally:
            log.info("Shutting down...")
            await manager_api_runner.cleanup()
            await client_api_runner.cleanup()


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=Path,
    default=None,
    help="The config file path. "
    "(default: ./storage-proxy.toml and /etc/backend.ai/storage-proxy.toml)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable the debug mode and override the global log level to DEBUG.",
)
@click.pass_context
def main(cli_ctx, config_path, debug):
    # Determine where to read configuration.
    raw_cfg, cfg_src_path = config.read_from_file(config_path, "storage-proxy")

    config.override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
    config.override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
    config.override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
    config.override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")
    if debug:
        config.override_key(raw_cfg, ("debug", "enabled"), True)

    try:
        local_config = config.check(raw_cfg, local_config_iv)
        local_config["_src"] = cfg_src_path
    except config.ConfigurationError as e:
        print(
            "ConfigurationError: Validation of agent configuration has failed:",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()

    if local_config["debug"]["enabled"]:
        config.override_key(local_config, ("logging", "level"), "DEBUG")
        config.override_key(local_config, ("logging", "pkg-ns", "ai.backend"), "DEBUG")

    # if os.getuid() != 0:
    #     print('Storage agent can only be run as root', file=sys.stderr)
    #     raise click.Abort()

    multiprocessing.set_start_method("spawn")

    if cli_ctx.invoked_subcommand is None:
        local_config["storage-proxy"]["pid-file"].write_text(str(os.getpid()))
        log_sockpath = Path(
            f"/tmp/backend.ai/ipc/storage-proxy-logger-{os.getpid()}.sock",
        )
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        local_config["logging"]["endpoint"] = log_endpoint
        try:
            logger = Logger(
                local_config["logging"],
                is_master=True,
                log_endpoint=log_endpoint,
            )
            with logger:
                setproctitle("backend.ai: storage-proxy")
                log.info("Backend.AI Storage Proxy", VERSION)
                log.info("Runtime: {0}", env_info())
                log.info("Node ID: {0}", local_config["storage-proxy"]["node-id"])
                log_config = logging.getLogger("ai.backend.agent.config")
                if local_config["debug"]["enabled"]:
                    log_config.debug("debug mode enabled.")
                if "debug" in local_config and local_config["debug"]["enabled"]:
                    print("== Storage proxy configuration ==")
                    pprint(local_config)
                if local_config["storage-proxy"]["event-loop"] == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                aiotools.start_server(
                    server_main_logwrapper,
                    num_workers=local_config["storage-proxy"]["num-proc"],
                    args=(local_config, log_endpoint),
                )
                log.info("exit.")
        finally:
            if local_config["storage-proxy"]["pid-file"].is_file():
                # check is_file() to prevent deleting /dev/null!
                local_config["storage-proxy"]["pid-file"].unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
