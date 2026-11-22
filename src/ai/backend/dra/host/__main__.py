from __future__ import annotations

import asyncio
import json
import logging
import signal
from pathlib import Path

import click

from ai.backend.dra.errors import IsolationRequiredError
from ai.backend.dra.host.isolation import (
    BAI_HOOK_DEFAULT_DISTRO,
    IsolationKind,
    IsolationProvider,
    isolation_provider,
)
from ai.backend.dra.host.plugin_host import DEFAULT_MOUNT_ROOT, PluginHost
from ai.backend.dra.host.server import serve
from ai.backend.logging.logger import LocalLogger
from ai.backend.logging.structured import StructuredLogger
from ai.backend.logging.types import LogLevel

# __spec__ is None when this module runs as `python -m`.
log = StructuredLogger(logging.getLogger("ai.backend.dra.host"))


async def _serve(
    plugin: str,
    plugin_config: dict[str, object],
    socket_path: Path,
    mount_root: Path,
    local_config: dict[str, object],
    shared: bool,
    isolation: IsolationProvider | None,
    dynamic_mig: bool,
) -> None:
    host = await PluginHost.start(
        plugin,
        plugin_config,
        local_config,
        mount_root,
        shared=shared,
        isolation=isolation,
        dynamic_mig=dynamic_mig,
    )
    runner = await serve(host, socket_path)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    try:
        await stop.wait()
    finally:
        await runner.cleanup()
        await host.close()
        log.info("plugin host stopped")


@click.command()
@click.option(
    "--plugin",
    envvar="BAI_DRA_PLUGIN",
    required=True,
    help="`module:Class` of the accelerator plugin, e.g. ai.backend.accelerator.mock.plugin:MockPlugin",
)
@click.option(
    "--plugin-config",
    envvar="BAI_DRA_PLUGIN_CONFIG",
    default="{}",
    help="The plugin's configuration (what the Agent reads from etcd), as JSON.",
)
@click.option(
    "--socket",
    "socket_path",
    envvar="BAI_DRA_BRIDGE_SOCKET",
    type=click.Path(path_type=Path),
    required=True,
)
@click.option(
    "--mount-root",
    envvar="BAI_DRA_MOUNT_ROOT",
    type=click.Path(path_type=Path),
    default=DEFAULT_MOUNT_ROOT,
    help="Node directory, mounted at the same path, for the files plugins mount into containers.",
)
@click.option(
    "--shared/--exclusive",
    envvar="BAI_DRA_SHARED",
    default=False,
    help="Publish devices that several claims split by `shares` capacity (needs --isolation).",
)
@click.option(
    "--isolation",
    envvar="BAI_DRA_ISOLATION",
    type=click.Choice([k.value for k in IsolationKind]),
    default=IsolationKind.NONE.value,
    help="What limits a shared allocation: hami-core, bai-hook (the enterprise CUDA plugin's hook) or none.",
)
@click.option(
    "--hami-lib-dir",
    envvar="BAI_DRA_HAMI_LIB_DIR",
    type=click.Path(path_type=Path),
    default=None,
    help="Node directory with HAMi-core's libvgpu.so and ld.so.preload (--isolation hami-core).",
)
@click.option(
    "--hook-distro",
    envvar="BAI_DRA_HOOK_DISTRO",
    default=BAI_HOOK_DEFAULT_DISTRO,
    help="The distro whose build of the plugin's hook library to inject (--isolation bai-hook).",
)
@click.option(
    "--var-base-path",
    envvar="BAI_DRA_VAR_BASE_PATH",
    type=click.Path(path_type=Path),
    default=Path("/var/lib/bai-dra/var"),
    help="Node directory, mounted at the same path, for the plugin's `agent.var-base-path` files (hook cache).",
)
@click.option(
    "--dynamic-mig/--no-dynamic-mig",
    envvar="BAI_DRA_DYNAMIC_MIG",
    default=False,
    help="The Go driver creates and publishes MIG devices; list whole GPUs only.",
)
@click.option(
    "--log-level",
    envvar="BACKENDAI_LOG_LEVEL",
    type=click.Choice([lv.name for lv in LogLevel]),
    default=LogLevel.INFO.name,
)
def main(
    plugin: str,
    plugin_config: str,
    socket_path: Path,
    mount_root: Path,
    shared: bool,
    isolation: str,
    hami_lib_dir: Path | None,
    hook_distro: str,
    var_base_path: Path,
    dynamic_mig: bool,
    log_level: str,
) -> None:
    provider = isolation_provider(
        IsolationKind(isolation), hami_lib_dir=hami_lib_dir, hook_distro=hook_distro
    )
    if shared and provider is None:
        raise IsolationRequiredError("--shared needs --isolation hami-core or bai-hook")
    local_config: dict[str, object] = {"agent": {"var-base-path": str(var_base_path)}}
    with LocalLogger(log_level=LogLevel[log_level]):
        asyncio.run(
            _serve(
                plugin,
                json.loads(plugin_config),
                socket_path,
                mount_root,
                local_config,
                shared,
                provider,
                dynamic_mig,
            )
        )


if __name__ == "__main__":
    main()
