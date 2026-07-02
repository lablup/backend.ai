"""Agent-facing composition of session network + container runtime (BEP-1055).

`ContainerdAgent` holds one of these. It bridges the data the manager sends
(``cluster_info["network_config"]`` = the CNINetworkPlugin's ``{backend, subnet, vni,
mtu}``) into the network subsystem, and composes:

- per-session setup/teardown via `SessionNetworkCoordinator` (vxlan/bridge + peers), and
- per-container launch/terminate via `ContainerdKernelOrchestrator`
  (runtime + `ContainerNetworkProvisioner`).

The runtime client and the network subsystem remain separate classes that never
reference each other; this facade and the orchestrator are the only composition points.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ai.backend.agent.containerd.orchestrator import ContainerdKernelOrchestrator, LaunchResult
from ai.backend.agent.containerd.runtime import ContainerdRuntimeClient
from ai.backend.agent.network.cni import CniRunner
from ai.backend.agent.network.coordinator import SessionNetworkCoordinator
from ai.backend.agent.network.provisioner import ContainerNetworkProvisioner
from ai.backend.common.network.types import (
    EndpointPlan,
    Member,
    NetworkBackendKind,
    SessionNetMeta,
)

if TYPE_CHECKING:
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
    from ai.backend.common.etcd import AbstractKVStore
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig

_DEFAULT_MTU = 1500


def session_net_meta_from_network_config(
    session_id: str, network_config: Mapping[str, Any]
) -> SessionNetMeta:
    """Parse the manager-provided network_config into a SessionNetMeta."""
    vni_raw = network_config.get("vni")
    return SessionNetMeta(
        session_id=session_id,
        subnet=network_config["subnet"],
        backend=NetworkBackendKind(network_config["backend"]),
        mtu=int(network_config.get("mtu") or _DEFAULT_MTU),
        vni=int(vni_raw) if vni_raw is not None else None,
    )


class ContainerdSessionNetwork:
    _coordinator: SessionNetworkCoordinator
    _orchestrator: ContainerdKernelOrchestrator
    _agent_id: str
    _host_ip: str

    def __init__(
        self,
        etcd: AbstractKVStore,
        *,
        agent_id: str,
        host_ip: str,
        backend: AbstractNetworkAgentPluginV2[Any],
        runtime: ContainerdRuntimeClient,
        cni_runner: CniRunner,
    ) -> None:
        self._agent_id = agent_id
        self._host_ip = host_ip
        self._coordinator = SessionNetworkCoordinator(etcd, backend, agent_id)
        self._orchestrator = ContainerdKernelOrchestrator(
            runtime, ContainerNetworkProvisioner(backend, cni_runner)
        )

    def _self_member(self, meta: SessionNetMeta) -> Member:
        return Member(
            agent_id=self._agent_id,
            host_ip=self._host_ip,
            vtep_ip=self._host_ip if meta.backend is NetworkBackendKind.VXLAN else None,
            ip_range=None,
        )

    async def ensure_session(
        self, session_id: str, network_config: Mapping[str, Any]
    ) -> SessionNetMeta:
        """Set up this node's data plane for the session (idempotent per session)."""
        meta = session_net_meta_from_network_config(session_id, network_config)
        await self._coordinator.start(meta, self._self_member(meta))
        return meta

    async def teardown_session(self, session_id: str) -> None:
        await self._coordinator.stop(session_id)

    async def launch_container(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: list[str],
        oci_spec: dict[str, Any],
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
    ) -> LaunchResult:
        return await self._orchestrator.launch(
            container_id,
            image_ref=image_ref,
            command=command,
            oci_spec=oci_spec,
            meta=meta,
            kernel_config=kernel_config,
            cluster_info=cluster_info,
        )

    async def terminate_container(
        self, container_id: str, *, plan: EndpointPlan, task_pid: int
    ) -> None:
        await self._orchestrator.terminate(container_id, plan=plan, task_pid=task_pid)
