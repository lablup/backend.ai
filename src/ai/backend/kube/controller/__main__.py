from __future__ import annotations

import asyncio
import logging
import signal
import socket

import click
from kubernetes_asyncio import client

from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import REDIS_CONTAINER_LOG, REDIS_STATISTICS_DB
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import ValkeyTarget
from ai.backend.kube.controller.logs import KernelLogSync
from ai.backend.kube.controller.manifests import ControllerSettings
from ai.backend.kube.controller.reconciler import SessionReconciler
from ai.backend.kube.controller.reporter import StatusReporter
from ai.backend.kube.controller.runner import SessionController
from ai.backend.kube.controller.stats import (
    ContainerMetrics,
    KubeletStatsClient,
    StatBridge,
)
from ai.backend.kube.crd.device import GPUAllocationPolicy
from ai.backend.kube.crd.scheduling import SokovanBindMode
from ai.backend.kube.events import make_event_producer
from ai.backend.kube.kubeconfig import load_kube_config, quiet_client_logs
from ai.backend.kube.leader import run_maybe_as_leader
from ai.backend.logging.logger import LocalLogger
from ai.backend.logging.structured import StructuredLogger
from ai.backend.logging.types import LogLevel

# __spec__ is None when this module runs as `python -m`.
log = StructuredLogger(logging.getLogger("ai.backend.kube.controller"))


async def _serve(
    settings: ControllerSettings,
    workers: int,
    events: tuple[str, str, str | None] | None,
    metrics_port: int,
    lease: tuple[str, str, str] | None,
    kubelet_insecure_tls: bool,
) -> None:
    await load_kube_config()
    reporter: StatusReporter | None = None
    producer: EventProducer | None = None
    log_client: ValkeyContainerLogClient | None = None
    stat_client: ValkeyStatClient | None = None
    if events is not None:
        agent_id, valkey_addr, valkey_password = events
        producer = await make_event_producer(
            agent_id, socket.gethostname(), valkey_addr, valkey_password
        )
        log_client = await ValkeyContainerLogClient.create(
            ValkeyTarget(addr=valkey_addr, password=valkey_password),
            db_id=REDIS_CONTAINER_LOG,
            human_readable_name="kube.container_log",
        )
        stat_client = await ValkeyStatClient.create(
            ValkeyTarget(addr=valkey_addr, password=valkey_password),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="kube.stat",
        )
    async with client.ApiClient() as api:
        if producer is not None and log_client is not None:
            reporter = StatusReporter(producer, KernelLogSync(api, log_client, producer))
        controller = SessionController(
            api, SessionReconciler(api, settings, reporter), workers=workers
        )
        # Every replica serves /metrics; a standby's is empty, as it collects nothing.
        metrics_runner = None
        bridge: StatBridge | None = None
        if events is not None and stat_client is not None:
            metrics = ContainerMetrics(events[0])
            metrics_runner = await metrics.serve(metrics_port)
            bridge = StatBridge(
                api,
                stat_client,
                metrics,
                kubelet=KubeletStatsClient(api, verify=not kubelet_insecure_tls),
            )

        async def work() -> None:
            stats_task = asyncio.create_task(bridge.run()) if bridge is not None else None
            try:
                await controller.run()
            finally:
                if stats_task is not None:
                    stats_task.cancel()

        log.info("session controller started", krunner_image=settings.krunner_image)
        run_task = asyncio.current_task()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            if run_task is not None:
                loop.add_signal_handler(sig, run_task.cancel)
        try:
            await run_maybe_as_leader(api, lease, work)
        except asyncio.CancelledError:
            log.info("session controller stopped")
        finally:
            if bridge is not None:
                await bridge.close()
            if metrics_runner is not None:
                await metrics_runner.cleanup()
            if stat_client is not None:
                await stat_client.close()
            if log_client is not None:
                await log_client.close()


@click.command()
@click.option("--krunner-image", envvar="BACKENDAI_KRUNNER_IMAGE", required=True)
@click.option("--system-namespace", envvar="BACKENDAI_SYSTEM_NAMESPACE", default="backendai-system")
@click.option("--kernel-uid", envvar="BACKENDAI_KERNEL_UID", type=int, default=1000)
@click.option("--kernel-gid", envvar="BACKENDAI_KERNEL_GID", type=int, default=1000)
@click.option("--workers", envvar="BACKENDAI_CONTROLLER_WORKERS", type=int, default=4)
@click.option(
    "--agent-id",
    envvar="BACKENDAI_GATEWAY_ID",
    default=None,
    help="Agent id of this cluster in the Manager (the gateway's); kernel events carry it.",
)
@click.option(
    "--valkey-addr",
    envvar="BACKENDAI_VALKEY_ADDR",
    default=None,
    help="Valkey of the control plane. Without it no kernel event is sent.",
)
@click.option("--valkey-password", envvar="BACKENDAI_VALKEY_PASSWORD", default=None)
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
    default=GPUAllocationPolicy.DRA.value,
    help="dra: devices through ResourceClaims; device-plugin: NVIDIA GPUs as extended resources.",
)
@click.option(
    "--metrics-port",
    envvar="BACKENDAI_METRICS_PORT",
    type=int,
    default=9100,
    help="Port of /metrics with the kernels' utilization (with --valkey-addr).",
)
@click.option(
    "--kubelet-insecure-tls/--no-kubelet-insecure-tls",
    envvar="BACKENDAI_KUBELET_INSECURE_TLS",
    default=False,
    help="Do not verify the kubelets' serving certificates (self-signed ones) for kernel stats.",
)
@click.option(
    "--kueue-cluster-queue",
    envvar="BACKENDAI_KUEUE_CLUSTER_QUEUE",
    default="backendai",
    help="ClusterQueue the LocalQueues of sessions on the kueue scheduler point to.",
)
@click.option(
    "--leader-election/--no-leader-election",
    envvar="BACKENDAI_LEADER_ELECTION",
    default=False,
    help="Run as one of several replicas; the Lease holder reconciles.",
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
    krunner_image: str,
    system_namespace: str,
    kernel_uid: int,
    kernel_gid: int,
    workers: int,
    agent_id: str | None,
    valkey_addr: str | None,
    valkey_password: str | None,
    bind_mode: str,
    gpu_allocation_policy: str,
    metrics_port: int,
    kubelet_insecure_tls: bool,
    kueue_cluster_queue: str,
    leader_election: bool,
    lease_namespace: str,
    identity: str,
    log_level: str,
) -> None:
    lease = (lease_namespace, "session-controller", identity) if leader_election else None
    if (agent_id is None) != (valkey_addr is None):
        raise click.UsageError("--agent-id and --valkey-addr go together")
    events = (agent_id, valkey_addr, valkey_password) if agent_id and valkey_addr else None
    settings = ControllerSettings(
        krunner_image=krunner_image,
        system_namespace=system_namespace,
        kernel_uid=kernel_uid,
        kernel_gid=kernel_gid,
        bind_mode=SokovanBindMode(bind_mode),
        gpu_allocation_policy=GPUAllocationPolicy(gpu_allocation_policy),
        kueue_cluster_queue=kueue_cluster_queue,
    )
    with LocalLogger(log_level=LogLevel[log_level]):
        quiet_client_logs()
        asyncio.run(_serve(settings, workers, events, metrics_port, lease, kubelet_insecure_tls))


if __name__ == "__main__":
    main()
