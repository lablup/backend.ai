"""Composition of containerd runtime + cluster network (BEP-1055).

The runtime (`ContainerdRuntimeClient`) and the network subsystem
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

from ai.backend.agent.containerd.runtime import ContainerdRuntimeClient, TaskHandle
from ai.backend.common.network.types import EndpointPlan, SessionNetMeta

if TYPE_CHECKING:
    from ai.backend.agent.network.provisioner import ContainerNetworkProvisioner
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig


@dataclass(frozen=True)
class LaunchResult:
    handle: TaskHandle
    plan: EndpointPlan


class ContainerdKernelOrchestrator:
    """Combines the containerd runtime and the network provisioner for one container.

    Neither collaborator knows about the other; ordering and the netns/PID handoff live
    here and nowhere else.
    """

    _runtime: ContainerdRuntimeClient
    _network: ContainerNetworkProvisioner

    def __init__(
        self,
        runtime: ContainerdRuntimeClient,
        network: ContainerNetworkProvisioner,
    ) -> None:
        self._runtime = runtime
        self._network = network

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
        # 1) runtime: create the container with an empty netns, then start its task
        await self._runtime.create_container(
            container_id, image_ref=image_ref, command=command, oci_spec=oci_spec
        )
        handle = await self._runtime.start_container(container_id)
        # 2) hand the task's netns/PID to the network layer to attach CNI
        plan = await self._network.attach(
            kernel_config,
            cluster_info,
            meta=meta,
            container_id=container_id,
            task_pid=handle.pid,
        )
        return LaunchResult(handle=handle, plan=plan)

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
