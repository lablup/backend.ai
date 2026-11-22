from __future__ import annotations

import asyncio
import logging
import signal

import click
from aiohttp import web

from ai.backend.kube.nodehelper.server import build_app
from ai.backend.logging.logger import LocalLogger
from ai.backend.logging.structured import StructuredLogger
from ai.backend.logging.types import LogLevel

# __spec__ is None when this module runs as `python -m`.
log = StructuredLogger(logging.getLogger("ai.backend.kube.nodehelper"))


async def _serve(port: int, nerdctl: str, token: str) -> None:
    runner = web.AppRunner(build_app(nerdctl, token), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    log.info("node helper listening", port=port)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    try:
        await stop.wait()
    finally:
        await runner.cleanup()


@click.command()
@click.option("--port", envvar="BACKENDAI_NODE_HELPER_PORT", type=int, default=6090)
@click.option("--nerdctl", envvar="BACKENDAI_NERDCTL", default="/usr/local/bin/nerdctl")
@click.option("--token", envvar="BACKENDAI_NODE_HELPER_TOKEN", required=True)
@click.option(
    "--log-level",
    envvar="BACKENDAI_LOG_LEVEL",
    type=click.Choice([lv.name for lv in LogLevel]),
    default=LogLevel.INFO.name,
)
def main(port: int, nerdctl: str, token: str, log_level: str) -> None:
    with LocalLogger(log_level=LogLevel[log_level]):
        asyncio.run(_serve(port, nerdctl, token))


if __name__ == "__main__":
    main()
