from __future__ import annotations

import asyncio
import json
import logging
import signal
from pathlib import Path

import click

from ai.backend.dra.errors import IsolationRequiredError
from ai.backend.dra.host.isolation import HamiCore
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
    shared: bool,
    isolation: HamiCore | None,
) -> None:
    host = await PluginHost.start(
        plugin, plugin_config, {}, mount_root, shared=shared, isolation=isolation
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
    help="Publish devices that several claims split by `shares` capacity (needs --hami-lib-dir).",
)
@click.option(
    "--hami-lib-dir",
    envvar="BAI_DRA_HAMI_LIB_DIR",
    type=click.Path(path_type=Path),
    default=None,
    help="Node directory with HAMi-core's libvgpu.so and ld.so.preload; isolates shared devices.",
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
    hami_lib_dir: Path | None,
    log_level: str,
) -> None:
    isolation = HamiCore(hami_lib_dir) if hami_lib_dir is not None else None
    if shared and isolation is None:
        raise IsolationRequiredError("--shared needs an isolation provider (--hami-lib-dir)")
    with LocalLogger(log_level=LogLevel[log_level]):
        asyncio.run(
            _serve(plugin, json.loads(plugin_config), socket_path, mount_root, shared, isolation)
        )


if __name__ == "__main__":
    main()
