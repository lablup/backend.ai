"""Composition of containerd runtime + cluster network (BEP-1078).

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
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ai.backend.agent.errors.network import ContainerLifecycleUnavailable
from ai.backend.agent.network.runtime import OciRuntime, TaskHandle
from ai.backend.common.network.types import EndpointPlan, NetworkRole, SessionNetMeta

if TYPE_CHECKING:
    from ai.backend.agent.network.provisioner import ContainerNetworkProvisioner
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig


@dataclass(frozen=True)
class AttachResult:
    """What attaching one container to its session network produced."""

    plan: EndpointPlan
    endpoint_ips: dict[NetworkRole, str]

    @property
    def local_ip(self) -> str | None:
        """The host-reachable LOCAL IP — the address the agent uses to reach the kernel."""
        return self.endpoint_ips.get(NetworkRole.LOCAL)


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

    #: None for a backend that starts and stops its own containers and only borrows the network
    #: half — see `attach`. The methods that need it say so rather than failing on None.
    _runtime: OciRuntime | None
    _network: ContainerNetworkProvisioner

    def __init__(
        self,
        runtime: OciRuntime | None,
        network: ContainerNetworkProvisioner,
    ) -> None:
        self._runtime = runtime
        self._network = network

    def _require_runtime(self) -> OciRuntime:
        if self._runtime is None:
            raise ContainerLifecycleUnavailable(
                "this orchestrator was built without a container runtime; the backend that built"
                " it starts and stops its own containers"
            )
        return self._runtime

    async def create(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: dict[str, Any],
    ) -> None:
        """Create the container with an isolated (empty) netns; not started."""
        await self._require_runtime().create_container(
            container_id, image_ref=image_ref, command=command, oci_spec=oci_spec
        )

    async def start_and_attach(
        self,
        container_id: str,
        *,
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        on_planned: Callable[[EndpointPlan, int], None] | None = None,
    ) -> LaunchResult:
        """Create the (already-created container's) task, attach CNI to its netns, then start it.

        The attach happens while the task is in the 'created' state — its netns exists but the
        user command has not exec'd — so the container process begins with its network already
        in place. Attaching after start would race krunner's network-dependent init (REPL bind,
        SSH, peer lookup).

        ``on_planned`` receives ``(plan, task_pid)`` -- the detach inputs -- as soon as the plan
        exists and before anything is applied. The PID is the orchestrator's to hand over: it
        comes from the task this method creates, so a caller could not have it any earlier."""
        handle = await self._require_runtime().create_task(container_id)

        def planned(plan: EndpointPlan) -> None:
            if on_planned is not None:
                on_planned(plan, handle.pid)

        # attach is atomic (it rolls back its own partial ADDs on failure), so a failure here
        # leaves the network clean and the created task is reclaimed by the normal clean path.
        plan, endpoint_ips = await self._network.attach(
            kernel_config,
            cluster_info,
            meta=meta,
            container_id=container_id,
            task_pid=handle.pid,
            on_planned=planned,
        )
        try:
            await self._require_runtime().start_task(container_id)
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
        on_planned: Callable[[EndpointPlan, int], None] | None = None,
    ) -> LaunchResult:
        """Convenience: create then start+attach in one call (single-step callers)."""
        await self.create(container_id, image_ref=image_ref, command=command, oci_spec=oci_spec)
        return await self.start_and_attach(
            container_id,
            meta=meta,
            kernel_config=kernel_config,
            cluster_info=cluster_info,
            on_planned=on_planned,
        )

    async def attach(
        self,
        container_id: str,
        *,
        meta: SessionNetMeta,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        task_pid: int,
        on_planned: Callable[[EndpointPlan, int], None] | None = None,
    ) -> AttachResult:
        """Attach an already-running container's netns, given its PID.

        The half of `start_and_attach` that does not touch the runtime, for a backend that starts
        its own containers. It is safe to call after the container is running only because that
        container is held at a gate: its namespaces exist and its PID is final, but its command has
        not run, which is the same window `create_task` opens on containerd. Attaching a container
        that is already executing would race the runner's network-dependent init.

        The caller releases the gate afterwards, and owns the rollback if it cannot: attach is
        atomic in itself (it undoes its own partial ADDs), but a gate never released leaves a
        container parked forever.
        """

        def planned(plan: EndpointPlan) -> None:
            if on_planned is not None:
                on_planned(plan, task_pid)

        plan, endpoint_ips = await self._network.attach(
            kernel_config,
            cluster_info,
            meta=meta,
            container_id=container_id,
            task_pid=task_pid,
            on_planned=planned,
        )
        return AttachResult(plan=plan, endpoint_ips=endpoint_ips)

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
        await self._require_runtime().kill_container(container_id, signal=signal)
        await self._require_runtime().remove_container(container_id)
