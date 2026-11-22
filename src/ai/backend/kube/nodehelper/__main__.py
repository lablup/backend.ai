from __future__ import annotations

import asyncio
import logging
import os
import signal

import click
from aiohttp import web
from kubernetes_asyncio import client

from ai.backend.kube.kubeconfig import load_kube_config, quiet_client_logs
from ai.backend.kube.nodehelper.server import NODE_HELPER_TOKEN_ENV, build_app, kube_verifier
from ai.backend.logging.logger import LocalLogger
from ai.backend.logging.structured import StructuredLogger
from ai.backend.logging.types import LogLevel

# __spec__ is None when this module runs as `python -m`.
log = StructuredLogger(logging.getLogger("ai.backend.kube.nodehelper"))


async def _serve(port: int, nerdctl: str, token: str, node_name: str | None) -> None:
    await load_kube_config()
    async with client.ApiClient() as api:
        app = build_app(nerdctl, token, kube_verifier(nerdctl, api, node_name))
        runner = web.AppRunner(app, access_log=None)
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
@click.option(
    "--node-name",
    envvar="NODE_NAME",
    default=None,
    help="The node this helper runs on; a commit of a container elsewhere is refused.",
)
@click.option(
    "--log-level",
    envvar="BACKENDAI_LOG_LEVEL",
    type=click.Choice([lv.name for lv in LogLevel]),
    default=LogLevel.INFO.name,
)
def main(port: int, nerdctl: str, node_name: str | None, log_level: str) -> None:
    # Only from the environment (a Secret): an argument would show in the process list.
    token = os.environ.get(NODE_HELPER_TOKEN_ENV)
    if not token:
        raise click.UsageError(f"{NODE_HELPER_TOKEN_ENV} is not set")
    with LocalLogger(log_level=LogLevel[log_level]):
        quiet_client_logs()
        asyncio.run(_serve(port, nerdctl, token, node_name))


if __name__ == "__main__":
    main()
