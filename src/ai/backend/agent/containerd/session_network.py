"""Agent-facing composition of session network + container runtime (BEP-1058).

`ContainerdAgent` holds one of these. It bridges the data the manager sends
(``cluster_info["network_config"]`` = the CNINetworkPlugin's ``{backend, subnet, vni,
mtu}``) into the network subsystem, resolves the **per-session** data-plane backend
(vxlan / host-gw / wireguard) by name, and composes:

- per-session setup/teardown via `SessionNetworkCoordinator` (bridge + peers), and
- per-container launch/terminate via `ContainerdKernelOrchestrator`
  (runtime + `ContainerNetworkProvisioner`).

The runtime client and the network subsystem remain separate classes that never
reference each other; this facade and the orchestrator are the only composition points.
Each backend is instantiated per session with the backend the manager selected.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ai.backend.agent.containerd.orchestrator import ContainerdKernelOrchestrator, LaunchResult
from ai.backend.agent.containerd.runtime.interface import OciRuntime
from ai.backend.agent.containerd.session_tracker import SessionContainerTracker, TeardownScope
from ai.backend.agent.network.cni import CniRunner
from ai.backend.agent.network.coordinator import SessionNetworkCoordinator
from ai.backend.agent.network.provisioner import ContainerNetworkProvisioner
from ai.backend.common.network.types import (
    EndpointPlan,
    Member,
    NetworkBackendKind,
    SessionNetMeta,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
    from ai.backend.common.etcd import AbstractKVStore
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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


class UnknownNetworkBackend(RuntimeError):
    pass


class ContainerdSessionNetwork:
    _etcd: AbstractKVStore
    _agent_id: str
    _host_ip: str
    _runtime: OciRuntime
    _cni_runner: CniRunner
    _backends: Mapping[str, AbstractNetworkAgentPluginV2[Any]]
    _coordinators: dict[str, SessionNetworkCoordinator]
    _orchestrators: dict[str, ContainerdKernelOrchestrator]
    # Tracks container<->session so the last kernel's removal deterministically tears the
    # session network down (otherwise overlay devices + etcd members leak).
    _tracker: SessionContainerTracker

    def __init__(
        self,
        etcd: AbstractKVStore,
        *,
        agent_id: str,
        host_ip: str,
        runtime: OciRuntime,
        cni_runner: CniRunner,
        backends: Mapping[str, AbstractNetworkAgentPluginV2[Any]],
    ) -> None:
        self._etcd = etcd
        self._agent_id = agent_id
        self._host_ip = host_ip
        self._runtime = runtime
        self._cni_runner = cni_runner
        self._backends = backends
        self._coordinators = {}
        self._orchestrators = {}
        self._tracker = SessionContainerTracker()

    async def open(self) -> None:
        """Open the runtime client (e.g. establish the containerd gRPC channel)."""
        await self._runtime.open()

    async def close(self) -> None:
        await self._runtime.close()

    def _resolve_backend(self, meta: SessionNetMeta) -> AbstractNetworkAgentPluginV2[Any]:
        try:
            return self._backends[str(meta.backend)]
        except KeyError:
            raise UnknownNetworkBackend(
                f"no data-plane backend registered for '{meta.backend}' "
                f"(available: {sorted(self._backends)})"
            ) from None

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
        """Resolve the session's backend, set up this node's data plane, publish
        membership, and register the per-session coordinator + orchestrator."""
        meta = session_net_meta_from_network_config(session_id, network_config)
        if session_id in self._coordinators:
            # Already set up on this node (e.g. a second kernel of the same session placed
            # here). Session-network setup is per node, not per kernel — do it once.
            return meta
        backend = self._resolve_backend(meta)
        coordinator = SessionNetworkCoordinator(self._etcd, backend, self._agent_id)
        orchestrator = ContainerdKernelOrchestrator(
            self._runtime, ContainerNetworkProvisioner(backend, self._cni_runner)
        )
        # Register only AFTER a successful start, so a partial failure (which raises here)
        # doesn't leave a half-set-up coordinator that the idempotency check above would
        # then skip on retry — a retry must re-run the full setup cleanly.
        await coordinator.start(meta, self._self_member(meta))
        self._coordinators[session_id] = coordinator
        self._orchestrators[session_id] = orchestrator
        return meta

    async def teardown_session(self, session_id: str) -> None:
        coordinator = self._coordinators.pop(session_id, None)
        self._orchestrators.pop(session_id, None)
        if coordinator is not None:
            await coordinator.stop(session_id)

    async def launch_container(
        self,
        session_id: str,
        container_id: str,
        *,
        image_ref: str,
        command: list[str],
        oci_spec: dict[str, Any],
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
    ) -> LaunchResult:
        result = await self._orchestrators[session_id].launch(
            container_id,
            image_ref=image_ref,
            command=command,
            oci_spec=oci_spec,
            meta=meta,
            kernel_config=kernel_config,
            cluster_info=cluster_info,
        )
        self._tracker.track(session_id, container_id)
        return result

    async def create_container(
        self,
        session_id: str,
        container_id: str,
        *,
        image_ref: str,
        command: list[str],
        oci_spec: dict[str, Any],
    ) -> None:
        """Create the container (not started) — maps to AbstractAgent.prepare_container."""
        await self._orchestrators[session_id].create(
            container_id, image_ref=image_ref, command=command, oci_spec=oci_spec
        )
        self._tracker.track(session_id, container_id)

    async def start_and_attach_container(
        self,
        session_id: str,
        container_id: str,
        *,
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
    ) -> LaunchResult:
        """Start the container + attach CNI — maps to AbstractAgent.start_container."""
        return await self._orchestrators[session_id].start_and_attach(
            container_id, meta=meta, kernel_config=kernel_config, cluster_info=cluster_info
        )

    async def terminate_container(
        self, session_id: str, container_id: str, *, plan: EndpointPlan, task_pid: int
    ) -> None:
        await self._orchestrators[session_id].terminate(container_id, plan=plan, task_pid=task_pid)

    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        return await self._runtime.image_entrypoint(image_ref)

    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        await self._runtime.pull_image(image_ref, auth=auth)

    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        await self._runtime.push_image(image_ref, auth=auth)

    async def remove_image(self, image_ref: str) -> None:
        await self._runtime.remove_image(image_ref)

    async def image_exists(self, image_ref: str) -> bool:
        return await self._runtime.image_exists(image_ref)

    async def image_digest(self, image_ref: str) -> str | None:
        return await self._runtime.image_digest(image_ref)

    async def kill_container(self, container_id: str, *, signal: int) -> None:
        await self._runtime.kill_container(container_id, signal=signal)

    async def remove_container(self, container_id: str) -> None:
        await self._runtime.remove_container(container_id)
        scope = self._tracker.untrack(container_id)
        if scope is not None:
            await self._teardown_session_network(scope)

    async def _teardown_session_network(self, scope: TeardownScope) -> None:
        """The last kernel of a session on this node is gone — tear its network down
        deterministically via the per-session coordinator (data-plane devices + etcd
        member). Best-effort: a teardown failure must not break kernel cleanup, but it is
        logged so leaks are visible."""
        try:
            if scope.session_id in self._coordinators:
                await self.teardown_session(scope.session_id)
        except Exception:
            log.exception("session network teardown failed for {}", scope.session_id)


def build_containerd_session_network(
    etcd: AbstractKVStore,
    *,
    agent_id: str,
    host_ip: str,
    uplink: str = "eth0",
    cni_path: str = "/opt/cni/bin",
    runtime: OciRuntime | None = None,
    cni_runner: CniRunner | None = None,
    backends: Mapping[str, AbstractNetworkAgentPluginV2[Any]] | None = None,
) -> ContainerdSessionNetwork:
    """Assemble a ContainerdSessionNetwork with default real collaborators.

    Defaults: the native containerd gRPC runtime client, CniPluginRunner exec'ing CNI
    plugins under ``cni_path``, and both the vxlan (multi-node overlay) and bridge
    (single-node local) backends on ``uplink``. Any collaborator can be overridden (used by
    ContainerdAgent, and injectable in tests). Additional backends (host-gw / wireguard) are
    registered here as they land.
    """
    # Lazy imports: keep this facade module decoupled from the concrete runtime/backend.
    from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime
    from ai.backend.agent.network.backends.bridge import BridgeNetworkPlugin
    from ai.backend.agent.network.backends.vxlan import VxlanNetworkPlugin
    from ai.backend.agent.network.cni_runner import CniPluginRunner

    runtime = runtime or ContainerdGrpcRuntime(namespace="backend-ai")
    cni_runner = cni_runner or CniPluginRunner(cni_path=cni_path)
    if backends is None:
        backends = {
            str(NetworkBackendKind.VXLAN): VxlanNetworkPlugin({}, {}, uplink=uplink),
            str(NetworkBackendKind.BRIDGE): BridgeNetworkPlugin({}, {}, uplink=uplink),
        }
    return ContainerdSessionNetwork(
        etcd,
        agent_id=agent_id,
        host_ip=host_ip,
        runtime=runtime,
        cni_runner=cni_runner,
        backends=backends,
    )
