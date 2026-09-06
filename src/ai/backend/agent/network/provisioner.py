"""Per-container network provisioner (BEP-1078).

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
from ai.backend.common.network.types import EndpointPlan, NetworkRole, SessionNetMeta

if TYPE_CHECKING:
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig


class AttachFailed(Exception):
    """An attach that did not finish, carrying the plan describing what it may have left behind.

    The attacher undoes its own partial work and says what it could not; this is how the plan
    reaches a caller that has not been told it yet, so the leftovers have a name to be torn down
    by rather than waiting for an orphan sweep.
    """

    plan: EndpointPlan

    def __init__(self, plan: EndpointPlan) -> None:
        super().__init__("the container's network attach did not complete")
        self.plan = plan


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
    ) -> tuple[EndpointPlan, dict[NetworkRole, str]]:
        """Attach a running container (identified by its task PID) to its session network.

        Returns the applied plan (kept by the caller for later detach) and the assigned IP
        per interface role (LOCAL is the host-reachable control address; OVERLAY is for
        cross-node kernel traffic)."""
        plan = await self._backend.attach_endpoint(kernel_config, cluster_info, meta=meta)
        try:
            assigned = await self._attacher.attach(
                plan, container_id=container_id, netns=netns_path_for_pid(task_pid)
            )
        except BaseException as e:
            # The plan names the host veth, the address and the rules an attach puts on this host,
            # and until now the caller only learned it when the attach returned. A failed one --
            # or one whose own undo could not remove everything -- therefore left host state that
            # nothing knew the name of. Hand it out with the failure so teardown can retry it.
            raise AttachFailed(plan) from e
        return plan, assigned

    async def detach(self, plan: EndpointPlan, *, container_id: str, task_pid: int) -> None:
        await self._attacher.detach(
            plan, container_id=container_id, netns=netns_path_for_pid(task_pid)
        )
