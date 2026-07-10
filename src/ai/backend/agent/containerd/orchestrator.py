"""Composition of containerd runtime + cluster network (BEP-1058).

The runtime (`OciRuntime`) and the network subsystem
(`ContainerNetworkProvisioner`) are two completely separate classes that never
reference each other. This orchestrator is the ONLY place they meet: it creates the
task via the runtime, then hands the task's netns/PID to the network layer to attach
CNI, then starts the task. Per-session network setup (vxlan/bridge, peers) is the
SessionNetworkCoordinator's job and happens once before any container launch.
"""

from __future__ import annotations

import contextlib
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
        """Create the (already-created container's) task, attach CNI to its netns, then start it.

        The attach happens while the task is in the 'created' state — its netns exists but the
        user command has not exec'd — so the container process begins with its network already
        in place. Attaching after start would race krunner's network-dependent init (REPL bind,
        SSH, peer lookup)."""
        handle = await self._runtime.create_task(container_id)
        # attach is atomic (it rolls back its own partial ADDs on failure), so a failure here
        # leaves the network clean and the created task is reclaimed by the normal clean path.
        plan, endpoint_ips = await self._network.attach(
            kernel_config,
            cluster_info,
            meta=meta,
            container_id=container_id,
            task_pid=handle.pid,
        )
        try:
            await self._runtime.start_task(container_id)
        except Exception:
            # The network is fully attached but the task failed to start. The caller only records
            # the plan once this method returns, so it cannot detach for us — undo the attach here
            # so the host veth / IPAM lease / MASQ rule do not leak. Best-effort; re-raise.
            with contextlib.suppress(Exception):
                await self._network.detach(plan, container_id=container_id, task_pid=handle.pid)
            raise
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

    async def detach(self, container_id: str, *, plan: EndpointPlan, task_pid: int) -> None:
        """Detach the container's network only (host veth removal + IPAM/MASQ release).

        Used by the two-phase agent lifecycle (destroy=kill, then clean=remove): the kill
        already stopped the task, so clean detaches with the attach-time plan before the
        container is removed. Without this, host-local IPAM addresses and NAT rules leak."""
        await self._network.detach(plan, container_id=container_id, task_pid=task_pid)

    async def terminate(
        self,
        container_id: str,
        *,
        plan: EndpointPlan,
        task_pid: int,
        signal: int = signal_module.SIGKILL,
    ) -> None:
        # reverse order: detach network first, then tear down the runtime
        await self.detach(container_id, plan=plan, task_pid=task_pid)
        await self._runtime.kill_container(container_id, signal=signal)
        await self._runtime.remove_container(container_id)
