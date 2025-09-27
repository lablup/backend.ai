import asyncio
import logging
import multiprocessing
import os
import signal
import sys
from pathlib import Path
from pprint import pprint
from typing import Any, AsyncGenerator, Sequence

import aiotools
import click
from setproctitle import setproctitle

from ai.backend.common.config import (
    ConfigurationError,
)
from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.common.utils import env_info
from ai.backend.logging import BraceStyleAdapter, Logger, LogLevel

from .. import __version__ as VERSION
from .config import StorageProxyPrivilegedWorkerConfig, load_local_config

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@aiotools.server_context
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Sequence[Any],
) -> AsyncGenerator[None, signal.Signals]:
    from .bootstrap.main import (
        BootstrapProvisioner,
        BootstrapSpec,
        BootstrapSpecGenerator,
        BootstrapStage,
    )

    setproctitle(f"backend.ai: privileged-storage-proxy privileged-worker-{pidx}")

    local_config: StorageProxyPrivilegedWorkerConfig = _args[0]
    bootstrap_stage = BootstrapStage(BootstrapProvisioner())
    bootstrap_spec = BootstrapSpec(
        loop=loop,
        local_config=local_config,
        pidx=pidx,
    )
    await bootstrap_stage.setup(BootstrapSpecGenerator(bootstrap_spec))
    await bootstrap_stage.wait_for_resource()
    yield
    await bootstrap_stage.teardown()


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help=(
        "The config file path. "
        "(default: ./privileged-storage-proxy.toml and /etc/backend.ai/privileged-storage-proxy.toml)"
    ),
)
@click.option(
    "--debug",
    is_flag=True,
    help="A shortcut to set `--log-level=DEBUG`",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogLevel], case_sensitive=False),
    default=LogLevel.NOTSET,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    cli_ctx: click.Context,
    config_path: Path,
    log_level: LogLevel,
    debug: bool = False,
) -> int:
    """Start the root worker process for privileged-storage-proxy."""

    log_level = LogLevel.DEBUG if debug else log_level
    try:
        local_config = load_local_config(config_path, log_level=log_level)
    except ConfigurationError:
        print(
            "ConfigurationError: Could not read or validate the privileged-storage-proxy local config:",
            file=sys.stderr,
        )
        raise click.Abort()

    # Note: logging configuration is handled separately in Logger class
    # Debug mode is already set during config loading if needed

    multiprocessing.set_start_method("spawn")

    if cli_ctx.invoked_subcommand is None:
        local_config.storage_proxy.pid_file.write_text(str(os.getpid()))
        ipc_base_path = local_config.storage_proxy.ipc_base_path
        log_sockpath = Path(
            ipc_base_path / f"privileged-storage-proxy-logger-{os.getpid()}.sock",
        )
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        num_workers = local_config.storage_proxy.num_proc
        try:
            logger = Logger(
                local_config.logging,
                is_master=True,
                log_endpoint=log_endpoint,
                msgpack_options={
                    "pack_opts": DEFAULT_PACK_OPTS,
                    "unpack_opts": DEFAULT_UNPACK_OPTS,
                },
            )
            with logger:
                setproctitle("backend.ai: privileged-storage-proxy worker")
                log.info("Backend.AI Privileged Storage Proxy Worker", VERSION)
                log.info("Runtime: {0}", env_info())
                log.info("Node ID: {0}", local_config.storage_proxy.node_id)
                log_config = logging.getLogger("ai.backend.storage.config")
                if local_config.debug.enabled:
                    log_config.debug("debug mode enabled.")
                if local_config.debug.enabled:
                    print("== Storage proxy configuration ==")
                    pprint(local_config)
                if local_config.storage_proxy.event_loop == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")

                aiotools.start_server(
                    server_main_logwrapper,
                    num_workers=num_workers,
                    args=(local_config, log_endpoint),
                )
                log.info("exit.")
        finally:
            if local_config.storage_proxy.pid_file.is_file():
                # check is_file() to prevent deleting /dev/null!
                local_config.storage_proxy.pid_file.unlink()
    return 0
