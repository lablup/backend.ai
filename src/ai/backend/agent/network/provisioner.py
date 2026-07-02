"""Per-container network provisioner (BEP-1055).

The single entry point a containerd (or other host-native) runtime calls to wire a
container into its session network: ask the v2 backend for the container's
`EndpointPlan`, then apply it as a CNI chain against the container's network
namespace (derived from the task PID). Session-level setup (vxlan/bridge, peers)
is the SessionNetworkCoordinator's job and happens once per session before this.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ai.backend.agent.network.cni import CniAttacher, CniRunner
from ai.backend.agent.network.cni_runner import netns_path_for_pid
from ai.backend.common.network.types import EndpointPlan, SessionNetMeta

if TYPE_CHECKING:
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig


class ContainerNetworkProvisioner:
    _backend: AbstractNetworkAgentPluginV2[Any]
    _attacher: CniAttacher

    def __init__(
        self,
        backend: AbstractNetworkAgentPluginV2[Any],
        cni_runner: CniRunner,
    ) -> None:
        self._backend = backend
        self._attacher = CniAttacher(cni_runner)

    async def attach(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
        container_id: str,
        task_pid: int,
    ) -> EndpointPlan:
        """Attach a running container (identified by its task PID) to its session
        network and return the applied plan (kept by the caller for later detach)."""
        plan = await self._backend.attach_endpoint(kernel_config, cluster_info, meta=meta)
        await self._attacher.attach(
            plan, container_id=container_id, netns=netns_path_for_pid(task_pid)
        )
        return plan

    async def detach(
        self, plan: EndpointPlan, *, container_id: str, task_pid: int
    ) -> None:
        await self._attacher.detach(
            plan, container_id=container_id, netns=netns_path_for_pid(task_pid)
        )
