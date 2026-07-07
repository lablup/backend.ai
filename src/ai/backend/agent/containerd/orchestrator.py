"""Composition of containerd runtime + cluster network (BEP-1058).

The runtime (`OciRuntime`) and the network subsystem
(`ContainerNetworkProvisioner`) are two completely separate classes that never
reference each other. This orchestrator is the ONLY place they meet: it creates the
task via the runtime, then hands the task's netns/PID to the network layer to attach
CNI, then starts the task. Per-session network setup (vxlan/bridge, peers) is the
SessionNetworkCoordinator's job and happens once before any container launch.
"""

from __future__ import annotations

import signal as signal_module
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ai.backend.agent.containerd.runtime.interface import OciRuntime, TaskHandle
from ai.backend.common.network.types import EndpointPlan, NetworkRole, SessionNetMeta

if TYPE_CHECKING:
    from ai.backend.agent.network.provisioner import ContainerNetworkProvisioner
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig


@dataclass(frozen=True)
class LaunchResult:
    handle: TaskHandle
    plan: EndpointPlan
    endpoint_ips: dict[NetworkRole, str]

    @property
    def local_ip(self) -> str | None:
        """The host-reachable LOCAL IP — the address the agent uses to reach the kernel."""
        return self.endpoint_ips.get(NetworkRole.LOCAL)


class ContainerdKernelOrchestrator:
    """Combines the containerd runtime and the network provisioner for one container.

    Neither collaborator knows about the other; ordering and the netns/PID handoff live
    here and nowhere else.
    """

    _runtime: OciRuntime
    _network: ContainerNetworkProvisioner

    def __init__(
        self,
        runtime: OciRuntime,
        network: ContainerNetworkProvisioner,
    ) -> None:
        self._runtime = runtime
        self._network = network

    async def create(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: dict[str, Any],
    ) -> None:
        """Create the container with an isolated (empty) netns; not started."""
        await self._runtime.create_container(
            container_id, image_ref=image_ref, command=command, oci_spec=oci_spec
        )

    async def start_and_attach(
        self,
        container_id: str,
        *,
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
    ) -> LaunchResult:
        """Start the (already created) container's task, then attach CNI to its netns."""
        handle = await self._runtime.start_container(container_id)
        plan, endpoint_ips = await self._network.attach(
            kernel_config,
            cluster_info,
            meta=meta,
            container_id=container_id,
            task_pid=handle.pid,
        )
        return LaunchResult(handle=handle, plan=plan, endpoint_ips=endpoint_ips)

    async def launch(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: dict[str, Any],
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
    ) -> LaunchResult:
        """Convenience: create then start+attach in one call (single-step callers)."""
        await self.create(container_id, image_ref=image_ref, command=command, oci_spec=oci_spec)
        return await self.start_and_attach(
            container_id, meta=meta, kernel_config=kernel_config, cluster_info=cluster_info
        )

    async def terminate(
        self,
        container_id: str,
        *,
        plan: EndpointPlan,
        task_pid: int,
        signal: int = signal_module.SIGKILL,
    ) -> None:
        # reverse order: detach network first, then tear down the runtime
        await self._network.detach(plan, container_id=container_id, task_pid=task_pid)
        await self._runtime.kill_container(container_id, signal=signal)
        await self._runtime.remove_container(container_id)
