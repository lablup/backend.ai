from __future__ import annotations

import asyncio
import logging
import signal
import socket

import click
from kubernetes_asyncio import client

from ai.backend.common.types import AgentSelectionStrategy
from ai.backend.kube.crd.device import GPUAllocationPolicy
from ai.backend.kube.crd.scheduling import SokovanBindMode
from ai.backend.kube.kubeconfig import load_kube_config, quiet_client_logs
from ai.backend.kube.leader import run_maybe_as_leader
from ai.backend.kube.scheduler.runner import SokovanScheduler
from ai.backend.kube.scheduler.selection import SELECTABLE_STRATEGIES
from ai.backend.logging.logger import LocalLogger
from ai.backend.logging.structured import StructuredLogger
from ai.backend.logging.types import LogLevel

# __spec__ is None when this module runs as `python -m`.
log = StructuredLogger(logging.getLogger("ai.backend.kube.scheduler"))


async def _serve(
    interval: float,
    strategy: AgentSelectionStrategy,
    bind_mode: SokovanBindMode,
    policy: GPUAllocationPolicy,
    allocator_url: str,
    lease: tuple[str, str, str] | None,
) -> None:
    await load_kube_config()
    async with client.ApiClient() as api:
        scheduler = SokovanScheduler(
            api,
            interval=interval,
            strategy=strategy,
            bind_mode=bind_mode,
            policy=policy,
            allocator_url=allocator_url,
        )
        log.info(
            "sokovan scheduler started",
            strategy=str(strategy),
            bind_mode=str(bind_mode),
            gpu_allocation_policy=str(policy),
        )
        run_task = asyncio.current_task()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            if run_task is not None:
                loop.add_signal_handler(sig, run_task.cancel)
        try:
            await run_maybe_as_leader(api, lease, scheduler.run)
        except asyncio.CancelledError:
            log.info("sokovan scheduler stopped")


@click.command()
@click.option("--interval", envvar="BACKENDAI_SCHEDULER_INTERVAL", type=float, default=2.0)
@click.option(
    "--strategy",
    envvar="BACKENDAI_SCHEDULER_STRATEGY",
    type=click.Choice([s.value for s in SELECTABLE_STRATEGIES]),
    default=AgentSelectionStrategy.CONCENTRATED.value,
    help="Node selection, with the agent selectors of the Manager.",
)
@click.option(
    "--bind-mode",
    envvar="BACKENDAI_SOKOVAN_BIND_MODE",
    type=click.Choice([m.value for m in SokovanBindMode]),
    default=SokovanBindMode.GATE.value,
)
@click.option(
    "--gpu-allocation-policy",
    envvar="BACKENDAI_GPU_ALLOCATION_POLICY",
    type=click.Choice([p.value for p in GPUAllocationPolicy]),
    default=GPUAllocationPolicy.BAI.value,
    help="Who holds the NVIDIA GPUs: bai-dra (bai), the NVIDIA DRA driver (nvidia-dra), or the"
    " device plugin (device-plugin, whole GPUs only).",
)
@click.option(
    "--allocator-url",
    envvar="BACKENDAI_DRA_ALLOCATOR_URL",
    default="http://127.0.0.1:8786",
    help="The DRA allocator sidecar (binder mode).",
)
@click.option(
    "--leader-election/--no-leader-election",
    envvar="BACKENDAI_LEADER_ELECTION",
    default=False,
    help="Run as one of several replicas; the Lease holder schedules.",
)
@click.option("--lease-namespace", envvar="POD_NAMESPACE", default="backendai-system")
@click.option("--identity", envvar="POD_NAME", default=socket.gethostname())
@click.option(
    "--log-level",
    envvar="BACKENDAI_LOG_LEVEL",
    type=click.Choice([lv.name for lv in LogLevel]),
    default=LogLevel.INFO.name,
)
def main(
    interval: float,
    strategy: str,
    bind_mode: str,
    gpu_allocation_policy: str,
    allocator_url: str,
    leader_election: bool,
    lease_namespace: str,
    identity: str,
    log_level: str,
) -> None:
    lease = (lease_namespace, "sokovan-scheduler", identity) if leader_election else None
    with LocalLogger(log_level=LogLevel[log_level]):
        quiet_client_logs()
        asyncio.run(
            _serve(
                interval,
                AgentSelectionStrategy(strategy),
                SokovanBindMode(bind_mode),
                GPUAllocationPolicy(gpu_allocation_policy),
                allocator_url,
                lease,
            )
        )


if __name__ == "__main__":
    main()
