from __future__ import annotations

import asyncio
import logging
import os
import signal
import socket
from pathlib import Path

import click
from kubernetes_asyncio import client
from kubernetes_asyncio.stream import WsApiClient
from zmq.auth.certs import load_certificate

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.kube.controller.naming import LABEL_MANAGED_BY, MANAGED_BY
from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.session import SessionWorkload
from ai.backend.kube.events import make_event_producer
from ai.backend.kube.gateway.heartbeat import GatewayHeartbeat, GatewayIdentity
from ai.backend.kube.gateway.images import GatewayImages
from ai.backend.kube.gateway.kernel_index import (
    LABEL_NAMESPACE_MANAGED_BY,
    NAMESPACE_MANAGED_BY,
    KernelIndex,
)
from ai.backend.kube.gateway.kernels import GatewayKernels
from ai.backend.kube.gateway.server import GatewayRPCServer
from ai.backend.kube.kubeconfig import load_kube_config, quiet_client_logs
from ai.backend.kube.nodehelper.server import NODE_HELPER_TOKEN_ENV
from ai.backend.kube.watch import watch_forever
from ai.backend.logging.logger import LocalLogger
from ai.backend.logging.structured import StructuredLogger
from ai.backend.logging.types import LogLevel

# __spec__ is None when this module runs as `python -m`.
log = StructuredLogger(logging.getLogger("ai.backend.kube.gateway"))


async def _serve(
    gateway_id: str,
    bind: str,
    manager_public_key: Path,
    keypair: Path,
    valkey_addr: str,
    valkey_password: str | None,
    identity_args: tuple[str, str, str | None],
    node_helper: tuple[str, int, str] | None,
) -> None:
    await load_kube_config()
    manager_pkey, _ = load_certificate(str(manager_public_key))
    public_key, secret_key = load_certificate(str(keypair))
    if secret_key is None:
        raise click.UsageError(f"{keypair} has no secret key")
    event_producer = await make_event_producer(
        gateway_id, socket.gethostname(), valkey_addr, valkey_password
    )
    resource_group, advertised_addr, region = identity_args
    identity = GatewayIdentity(resource_group, advertised_addr, public_key, region)
    index = KernelIndex(on_removed=lambda kernel_id: kernels.schedule_forget(kernel_id))
    async with client.ApiClient() as api, WsApiClient() as ws_api:
        kernels = GatewayKernels(index, api, ws_api, event_producer)
        core = client.CoreV1Api(api)
        custom = client.CustomObjectsApi(api)
        sw = SessionWorkload.crd
        images = (
            GatewayImages(
                api,
                index,
                event_producer,
                namespace=node_helper[0],
                port=node_helper[1],
                token=node_helper[2],
            )
            if node_helper is not None
            else None
        )
        server = GatewayRPCServer(
            kernels,
            images=images,
            gateway_id=gateway_id,
            bind=bind,
            manager_public_key=PublicKey(manager_pkey),
            public_key=PublicKey(public_key),
            secret_key=SecretKey(secret_key),
        )
        run_task = asyncio.current_task()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            if run_task is not None:
                loop.add_signal_handler(sig, run_task.cancel)
        try:
            async with server, asyncio.TaskGroup() as tg:
                tg.create_task(GatewayHeartbeat(api, event_producer, identity).run())
                # Only Pods in the namespaces the Manager created are kernels (KernelIndex).
                tg.create_task(
                    watch_forever(
                        lambda **kw: core.list_namespace(
                            label_selector=f"{LABEL_NAMESPACE_MANAGED_BY}={NAMESPACE_MANAGED_BY}",
                            **kw,
                        ),
                        index.apply_namespace,
                        on_relist=index.replace_namespaces,
                    )
                )
                # A kernel Pod counts only for the SessionWorkload (by uid) declaring its kernel.
                tg.create_task(
                    watch_forever(
                        lambda **kw: custom.list_cluster_custom_object(
                            sw.group, CRD_VERSION, sw.plural, **kw
                        ),
                        index.apply_workload,
                        on_relist=index.replace_workloads,
                    )
                )
                tg.create_task(
                    watch_forever(
                        lambda **kw: core.list_pod_for_all_namespaces(
                            label_selector=f"{LABEL_MANAGED_BY}={MANAGED_BY}", **kw
                        ),
                        index.apply,
                        on_relist=index.replace_pods,
                    )
                )
        except asyncio.CancelledError:
            log.info("session gateway stopped")
        finally:
            await kernels.close()
            await event_producer.close()


@click.command()
@click.option(
    "--gateway-id",
    envvar="BACKENDAI_GATEWAY_ID",
    required=True,
    help="Agent id of this cluster in the Manager; the kernels it runs belong to it.",
)
@click.option("--resource-group", envvar="BACKENDAI_RESOURCE_GROUP", required=True)
@click.option(
    "--advertised-addr",
    envvar="BACKENDAI_ADVERTISED_ADDR",
    required=True,
    help="tcp://host:port at which the Manager reaches this gateway.",
)
@click.option("--region", envvar="BACKENDAI_REGION", default="local")
@click.option("--rpc-listen-addr", envvar="BACKENDAI_RPC_LISTEN_ADDR", default="0.0.0.0:6001")
@click.option(
    "--manager-public-key",
    envvar="BACKENDAI_MANAGER_PUBLIC_KEY",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--keypair",
    envvar="BACKENDAI_GATEWAY_KEYPAIR",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--valkey-addr", envvar="BACKENDAI_VALKEY_ADDR", required=True)
@click.option("--valkey-password", envvar="BACKENDAI_VALKEY_PASSWORD", default=None)
@click.option("--node-helper-namespace", envvar="POD_NAMESPACE", default="backendai-system")
@click.option("--node-helper-port", envvar="BACKENDAI_NODE_HELPER_PORT", type=int, default=6090)
@click.option(
    "--log-level",
    envvar="BACKENDAI_LOG_LEVEL",
    type=click.Choice([lv.name for lv in LogLevel]),
    default=LogLevel.INFO.name,
)
def main(
    gateway_id: str,
    resource_group: str,
    advertised_addr: str,
    region: str | None,
    rpc_listen_addr: str,
    manager_public_key: Path,
    keypair: Path,
    valkey_addr: str,
    valkey_password: str | None,
    node_helper_namespace: str,
    node_helper_port: int,
    log_level: str,
) -> None:
    # Only from the environment (a Secret): an argument would show in the process list.
    # Shared with the node helpers; without it, session commit is not offered.
    node_helper_token = os.environ.get(NODE_HELPER_TOKEN_ENV) or None
    node_helper = (
        (node_helper_namespace, node_helper_port, node_helper_token) if node_helper_token else None
    )
    with LocalLogger(log_level=LogLevel[log_level]):
        quiet_client_logs()
        asyncio.run(
            _serve(
                gateway_id,
                rpc_listen_addr,
                manager_public_key,
                keypair,
                valkey_addr,
                valkey_password,
                (resource_group, advertised_addr, region),
                node_helper,
            )
        )


if __name__ == "__main__":
    main()
