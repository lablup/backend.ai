"""Per-container network provisioner (BEP-1078).

The single entry point a containerd (or other host-native) runtime calls to wire a
container into its session network: ask the v2 backend for the container's
`EndpointPlan`, then apply it as a CNI chain against the container's network
namespace (derived from the task PID). Session-level setup (vxlan/bridge, peers)
is the SessionNetworkCoordinator's job and happens once per session before this.

`ContainerNetworkProvisioner` is the protocol; `CniProvisioner` here is the in-process
implementation and `PrivNetProvisioner` (network/privnet/client.py) the privileged one.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from ai.backend.agent.errors.network import ContainerAttachFailed
from ai.backend.agent.network.cni import CniAttacher, CniRunner
from ai.backend.agent.network.cni_runner import netns_path_for_pid
from ai.backend.common.network.types import EndpointPlan, NetworkRole, SessionNetMeta

if TYPE_CHECKING:
    from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig


class ContainerNetworkProvisioner(Protocol):
    """The per-container attach/detach surface an orchestrator talks to.

    A protocol because there are two implementations and they share no code: `CniProvisioner`
    below, and `PrivNetProvisioner`, which forwards the same two verbs to the privileged helper.
    Typing the seam nominally is what let the two drift -- the privnet drop-in went a whole
    release without `on_planned` and every multi-node session died on a `TypeError` that no type
    check could see, because the factory that built it was annotated `Any`.
    """

    async def attach(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
        container_id: str,
        task_pid: int,
        on_planned: Callable[[EndpointPlan], None] | None = None,
    ) -> tuple[EndpointPlan, dict[NetworkRole, str]]:
        """Attach the container to its session network, returning the plan and per-role IPs.

        ``on_planned`` is handed the plan before anything is applied -- the only way a *cancelled*
        attach leaves the caller able to name its leftovers. Every implementation must call it.
        """
        ...

    async def detach(self, plan: EndpointPlan, *, container_id: str, task_pid: int) -> None:
        """Undo `attach` for one container, given the plan `attach` returned."""
        ...


class CniProvisioner:
    """`ContainerNetworkProvisioner` for a runtime this process drives itself: ask the v2 backend
    for the plan, then apply it as a CNI chain against the container's netns."""

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
        on_planned: Callable[[EndpointPlan], None] | None = None,
    ) -> tuple[EndpointPlan, dict[NetworkRole, str]]:
        plan = await self._backend.attach_endpoint(kernel_config, cluster_info, meta=meta)
        if on_planned is not None:
            on_planned(plan)
        try:
            assigned = await self._attacher.attach(
                plan, container_id=container_id, netns=netns_path_for_pid(task_pid)
            )
        except Exception as e:
            # Exception, and not BaseException: this used to catch cancellation too and hand the
            # caller a plain `Exception`, which threw away what `asyncio.timeout`, an agent
            # shutdown and a cancelled parent task all mean. Those propagate as themselves; only
            # a genuine failure is renamed, and it is renamed because an `ip` command's
            # `RuntimeError` reaching the manager names neither the container nor the session.
            raise ContainerAttachFailed(
                f"could not attach container {container_id} to the network of session"
                f" {meta.session_id}: {e}"
            ) from e
        return plan, assigned

    async def detach(self, plan: EndpointPlan, *, container_id: str, task_pid: int) -> None:
        await self._attacher.detach(
            plan, container_id=container_id, netns=netns_path_for_pid(task_pid)
        )
