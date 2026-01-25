"""
BEP-1016: NVIDIA GPU Plugin Example with Fabric Manager Integration

This pseudocode demonstrates how the proposed Accelerator Interface v2 APIs
would be implemented for NVIDIA GPUs, including integration with
nvidia-fabric-manager for NVSwitch topology management.

NOTE: This is pseudocode for illustration purposes. Some imports and
type definitions are assumed to exist in the actual implementation.
"""

from __future__ import annotations

import grp
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

# Assumed imports from the Backend.AI agent framework
# from ai.backend.agent.types import (
#     AbstractDeviceHostPlugin, AbstractDevicePlugin, AbstractLifecycleHook,
#     AbstractDevice, DeviceId, AgentId, SlotName, SlotDefinition, SlotType,
#     DeviceAllocation, Workload, WorkloadConfig, Mount,
#     StatContext, NodeMetrics, WorkloadMetrics, ProcessMetrics,
#     ServiceNotAvailableError, UnknownServiceError,
# )


# =============================================================================
# Supporting Types and Structs
# =============================================================================


@dataclass
class NvLinkInfo:
    """Information about an NVLink connection between two GPUs."""
    bandwidth_gbps: float
    version: int


@dataclass
class PcieBusInfo:
    """PCIe bus location information."""
    domain: int
    bus: int
    device: int
    function: int


@dataclass
class NvidiaDeviceTopology:
    """Structured representation of GPU interconnect topology."""
    gpu_ids: list[DeviceId]
    nvlink_connections: dict[tuple[DeviceId, DeviceId], NvLinkInfo]
    nvswitch_groups: list[set[DeviceId]]  # GPUs connected via same NVSwitch
    pcie_topology: dict[DeviceId, PcieBusInfo]


@dataclass
class NvidiaDevice:
    """NVIDIA GPU device information."""
    device_id: DeviceId
    hw_location: str
    hw_index: int
    numa_node: int
    memory_size: int
    # ... additional fields from BEP-1000


@dataclass
class NvidiaNodeInfo:
    """Node-level NVIDIA information."""
    driver_version: str
    cuda_version: int
    nvml_version: str
    fabric_manager_available: bool


@dataclass
class PartitionValidation:
    """Result of partition validation."""
    is_optimal: bool
    warnings: list[str]


# =============================================================================
# Fabric Manager Client
# =============================================================================


class NvidiaFabricManagerClient:
    """Client for interacting with nvidia-fabric-manager service."""

    def __init__(self, socket_path: str = "/var/run/nvidia-fabricmanager.sock"):
        self._socket_path = socket_path

    async def get_nvswitch_status(self) -> dict[str, Any]:
        """Query NVSwitch status from fabric manager."""
        ...

    async def configure_nvlink_for_gpus(
        self,
        gpu_ids: list[DeviceId],
        workload_id: str | None = None,
    ) -> None:
        """Request fabric manager to optimize NVLink routing for given GPUs."""
        ...

    async def notify_workload_start(
        self,
        workload_id: str,
        gpu_ids: list[DeviceId],
    ) -> None:
        """Notify fabric manager that a workload is starting on specified GPUs."""
        ...

    async def notify_workload_end(self, workload_id: str) -> None:
        """Notify fabric manager that a workload has terminated."""
        ...


# =============================================================================
# Node-level Plugin (AbstractDeviceHostPlugin)
# =============================================================================


class NvidiaDeviceHostPlugin(AbstractDeviceHostPlugin):
    """
    Node-level NVIDIA GPU plugin.
    Provides global view of all devices and manages host-level services.
    """

    def __init__(self):
        self._fabric_manager_client: NvidiaFabricManagerClient | None = None
        self._topology: NvidiaDeviceTopology | None = None

    async def init(self) -> None:
        """Initialize the plugin, called once during agent runtime startup."""
        # Initialize fabric manager client if available
        if Path("/var/run/nvidia-fabricmanager.sock").exists():
            self._fabric_manager_client = NvidiaFabricManagerClient()

        # Discover topology
        self._topology = await self._discover_topology()

    async def list_devices(self) -> list[NvidiaDevice]:
        """List all NVIDIA GPUs in the node."""
        devices = []
        for idx in range(pynvml.nvmlDeviceGetCount()):
            handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
            uuid = pynvml.nvmlDeviceGetUUID(handle)
            devices.append(NvidiaDevice(
                device_id=DeviceId(uuid),
                hw_location=f"GPU-{idx}",
                hw_index=idx,
                numa_node=pynvml.nvmlDeviceGetNumaNode(handle),
                memory_size=pynvml.nvmlDeviceGetMemoryInfo(handle).total,
            ))
        return devices

    async def configurable_slots(self) -> list[SlotDefinition]:
        """Return slot types this plugin can provide."""
        return [
            SlotDefinition(
                slot_name="cuda.device",
                slot_type=SlotType.COUNT,
                display_name="GPU",
                description="NVIDIA CUDA GPU device",
            ),
            SlotDefinition(
                slot_name="cuda.mem",
                slot_type=SlotType.BYTES,
                display_name="GPU Memory",
                description="NVIDIA GPU memory",
            ),
        ]

    async def get_node_info(self) -> NvidiaNodeInfo:
        """Return node-level NVIDIA information."""
        return NvidiaNodeInfo(
            driver_version=pynvml.nvmlSystemGetDriverVersion(),
            cuda_version=pynvml.nvmlSystemGetCudaDriverVersion(),
            nvml_version=pynvml.nvmlSystemGetNVMLVersion(),
            fabric_manager_available=self._fabric_manager_client is not None,
        )

    async def get_device_topology(self) -> NvidiaDeviceTopology:
        """Return GPU interconnect topology."""
        if self._topology is None:
            self._topology = await self._discover_topology()
        return self._topology

    def get_host_service_client(self, service_name: str) -> Any:
        """Return client for host-level services."""
        match service_name:
            case "fabric-manager":
                if self._fabric_manager_client is None:
                    raise ServiceNotAvailableError(
                        "nvidia-fabric-manager is not running"
                    )
                return self._fabric_manager_client
            case _:
                raise UnknownServiceError(f"Unknown service: {service_name}")

    async def gather_node_metrics(self, stat_ctx: StatContext) -> NodeMetrics:
        """Collect node-level GPU metrics."""
        total_util = 0
        total_mem_used = 0
        for idx in range(pynvml.nvmlDeviceGetCount()):
            handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            total_util += util.gpu
            total_mem_used += mem.used
        return NodeMetrics(
            avg_utilization=total_util / pynvml.nvmlDeviceGetCount(),
            total_memory_used=total_mem_used,
        )

    def create_agent_context(
        self,
        device_mask: frozenset[DeviceId],
    ) -> NvidiaDevicePlugin:
        """Create an agent-scoped plugin instance."""
        return NvidiaDevicePlugin(self, device_mask)

    async def get_recommended_partitions(
        self,
        num_agents: int,
    ) -> list[frozenset[DeviceId]] | None:
        """
        Return topology-aware partition recommendations.
        Partitions are aligned with NVSwitch group boundaries where possible.
        Returns None if topology-aware partitioning is not applicable.
        """
        if self._topology is None:
            return None

        nvswitch_groups = self._topology.nvswitch_groups
        if not nvswitch_groups:
            return None  # No NVSwitch topology, fall back to naive split

        # Try to distribute complete NVSwitch groups among agents
        if len(nvswitch_groups) < num_agents:
            # More agents than NVSwitch groups - need to split groups
            # Return None to fall back to naive split with a warning
            return None

        # Distribute NVSwitch groups among agents
        partitions: list[set[DeviceId]] = [set() for _ in range(num_agents)]
        for idx, group in enumerate(nvswitch_groups):
            agent_idx = idx % num_agents
            partitions[agent_idx].update(group)

        return [frozenset(p) for p in partitions]

    def validate_partition(
        self,
        device_ids: frozenset[DeviceId],
    ) -> PartitionValidation:
        """
        Validate if a partition respects hardware topology.
        Returns warnings if the partition splits NVSwitch groups.
        """
        warnings = []

        if self._topology and self._topology.nvswitch_groups:
            for group in self._topology.nvswitch_groups:
                intersection = device_ids & group
                if intersection and intersection != group:
                    # Partition splits this NVSwitch group
                    warnings.append(
                        f"Partition splits NVSwitch group {group}. "
                        f"Included: {intersection}, Excluded: {group - intersection}"
                    )

        return PartitionValidation(
            is_optimal=len(warnings) == 0,
            warnings=warnings,
        )

    async def _discover_topology(self) -> NvidiaDeviceTopology:
        """Discover NVLink/NVSwitch topology using NVML."""
        # Implementation would use pynvml to discover topology
        ...


# =============================================================================
# Agent-level Plugin (AbstractDevicePlugin)
# =============================================================================


class NvidiaDevicePlugin(AbstractDevicePlugin):
    """
    Agent-scoped NVIDIA GPU plugin.
    Only sees and manages devices within the assigned device_mask.
    """

    def __init__(
        self,
        host_plugin: NvidiaDeviceHostPlugin,
        device_mask: frozenset[DeviceId],
    ):
        self.host_plugin = host_plugin
        self.device_mask = device_mask
        self.agent_id: AgentId | None = None
        self._devices: list[NvidiaDevice] | None = None
        self._alloc_map: NvidiaAllocMap | None = None

    async def init(self, agent_id: AgentId) -> None:
        """Initialize the agent context."""
        self.agent_id = agent_id
        # Cache filtered device list
        all_devices = await self.host_plugin.list_devices()
        self._devices = [d for d in all_devices if d.device_id in self.device_mask]
        # Create allocation map for this agent's devices
        self._alloc_map = NvidiaAllocMap(self._devices)

    async def list_devices(self) -> list[NvidiaDevice]:
        """List devices assigned to this agent."""
        assert self._devices is not None
        return self._devices

    async def available_slots(self) -> dict[SlotName, Decimal]:
        """Return available slots within this agent's partition."""
        assert self._alloc_map is not None
        return self._alloc_map.get_available_slots()

    def create_alloc_map(self) -> NvidiaAllocMap:
        """Create allocation map for this agent's devices."""
        assert self._devices is not None
        return NvidiaAllocMap(self._devices)

    async def create_lifecycle_hook(
        self,
        workload: Workload,
        device_alloc: DeviceAllocation,
    ) -> NvidiaLifecycleHook:
        """Create a lifecycle hook with scoped context for workload management."""
        allocated_devices = self.alloc_to_devices(device_alloc)
        allocated_ids = frozenset(d.device_id for d in allocated_devices)

        # Get topology for scoped view
        topology = await self.host_plugin.get_device_topology()

        # Create scoped context - hook cannot access beyond this scope
        context = LifecycleHookContext(
            workload=workload,
            device_alloc=device_alloc,
            agent_id=self.agent_id,
            allocated_devices=tuple(allocated_devices),
            topology_view=ScopedTopologyView(topology, allocated_ids),
            host_services=ScopedHostServices(
                self.host_plugin, workload, allocated_ids
            ),
        )

        return NvidiaLifecycleHook(context)

    def alloc_to_devices(
        self,
        device_alloc: DeviceAllocation,
    ) -> list[NvidiaDevice]:
        """Extract device list from allocation."""
        assert self._devices is not None
        alloc_ids = set(device_alloc.device_ids)
        return [d for d in self._devices if d.device_id in alloc_ids]

    async def gather_workload_metrics(
        self,
        stat_ctx: StatContext,
        workload_id: str,
    ) -> WorkloadMetrics:
        """Collect metrics for a specific workload."""
        # Use NVML to get per-process GPU utilization
        ...

    async def gather_process_metrics(
        self,
        stat_ctx: StatContext,
        pid: int,
    ) -> ProcessMetrics:
        """Collect metrics for a specific process."""
        ...


# =============================================================================
# Lifecycle Hook Context and Scoped Access Classes
# =============================================================================


@dataclass(frozen=True)
class LifecycleHookContext:
    """
    Scoped context for lifecycle hooks with controlled access.

    This context ensures that lifecycle hooks cannot affect other agents'
    workloads or access devices outside their allocation.
    """

    # === Basic information (read-only) ===
    workload: Workload
    device_alloc: DeviceAllocation
    agent_id: AgentId

    # === Allocated device information ===
    allocated_devices: tuple[AbstractDevice, ...]

    # === Scoped topology view ===
    topology_view: ScopedTopologyView

    # === Scoped host service access ===
    host_services: ScopedHostServices


class ScopedTopologyView:
    """
    Topology view restricted to allocated devices.

    Provides topology information filtered to only show connections
    between devices that are part of the current allocation.
    """

    def __init__(
        self,
        full_topology: NvidiaDeviceTopology,
        allocated_device_ids: frozenset[DeviceId],
    ):
        self._full_topology = full_topology
        self._allocated_ids = allocated_device_ids

    def get_nvlink_peers(self, device_id: DeviceId) -> list[DeviceId]:
        """Get NVLink peers, but only those within allocated devices."""
        if device_id not in self._allocated_ids:
            raise PermissionError(f"Device {device_id} not in allocation")
        all_peers = self._full_topology.nvlink_connections.get(device_id, [])
        # Return only peers within the allocation
        return [p for p in all_peers if p in self._allocated_ids]

    def are_devices_nvswitch_connected(self) -> bool:
        """Check if all allocated devices share an NVSwitch group."""
        for group in self._full_topology.nvswitch_groups:
            if self._allocated_ids.issubset(group):
                return True
        return False


class ScopedHostServices:
    """
    Host service access restricted to allocated devices.

    Provides controlled access to host-level services like fabric-manager,
    ensuring that operations are scoped to the current workload's devices.
    """

    def __init__(
        self,
        host_plugin: AbstractDeviceHostPlugin,
        workload: Workload,
        allocated_device_ids: frozenset[DeviceId],
    ):
        self._host_plugin = host_plugin
        self._workload = workload
        self._allocated_ids = allocated_device_ids

    async def configure_nvlink(self) -> None:
        """Configure NVLink for allocated devices only."""
        try:
            client = self._host_plugin.get_host_service_client("fabric-manager")
            # Can only configure for this workload's allocated devices
            await client.configure_nvlink_for_gpus(
                list(self._allocated_ids),
                workload_id=self._workload.id,  # For audit tracking
            )
        except ServiceNotAvailableError:
            pass

    async def notify_workload_starting(self) -> None:
        """Notify fabric manager that this workload is starting."""
        try:
            client = self._host_plugin.get_host_service_client("fabric-manager")
            await client.notify_workload_start(
                self._workload.id,
                list(self._allocated_ids),
            )
        except ServiceNotAvailableError:
            pass

    async def notify_workload_ended(self) -> None:
        """Notify fabric manager that this workload has ended."""
        try:
            client = self._host_plugin.get_host_service_client("fabric-manager")
            await client.notify_workload_end(self._workload.id)
        except ServiceNotAvailableError:
            pass

    # NOTE: No direct access to host_plugin - only specific, scoped APIs are exposed


# =============================================================================
# Workload-level Lifecycle Hook
# =============================================================================


class NvidiaLifecycleHook(AbstractLifecycleHook):
    """
    Lifecycle hook for NVIDIA GPU workloads.

    Uses LifecycleHookContext for scoped, secure access to host services.
    Cannot access devices outside the allocation or affect other workloads.
    """

    def __init__(self, context: LifecycleHookContext):
        self.ctx = context

    async def pre_create(self) -> WorkloadConfig:
        """
        Prepare workload configuration before container/process creation.
        This includes setting up fabric manager and generating mount/env configs.
        """
        # --- Fabric Manager Integration (via scoped services) ---
        # Check topology using scoped view (only sees allocated devices)
        if self.ctx.topology_view.are_devices_nvswitch_connected():
            # Configure NVLink (only for this workload's devices)
            await self.ctx.host_services.configure_nvlink()

        # Notify workload starting
        await self.ctx.host_services.notify_workload_starting()

        # --- Generate Workload Configuration ---
        allocated_devices = self.ctx.allocated_devices
        driver_version = "535.104.05"  # Would be obtained from host_plugin

        return WorkloadConfig(
            mounts=[
                # NVIDIA device files (dynamically generated based on allocation)
                *[
                    Mount(
                        f"/dev/nvidia{d.hw_index}",
                        f"/dev/nvidia{d.hw_index}",
                        type="device",
                    )
                    for d in allocated_devices
                ],
                Mount("/dev/nvidiactl", "/dev/nvidiactl", type="device"),
                Mount("/dev/nvidia-uvm", "/dev/nvidia-uvm", type="device"),
                # NVIDIA driver libraries (version-specific path)
                Mount(
                    f"/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.{driver_version}",
                    "/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1",
                    readonly=True,
                ),
            ],
            env_vars={
                "NVIDIA_VISIBLE_DEVICES": ",".join(
                    str(d.hw_location) for d in allocated_devices
                ),
                "NVIDIA_DRIVER_CAPABILITIES": "compute,utility",
                "CUDA_VISIBLE_DEVICES": ",".join(
                    str(i) for i in range(len(allocated_devices))
                ),
                # For NCCL/multi-GPU communication
                "NCCL_DEBUG": "INFO",
                "NCCL_IB_DISABLE": "0",
            },
            resource_data={
                "cuda.device": str(len(allocated_devices)),
                "cuda.mem": str(sum(d.memory_size for d in allocated_devices)),
                "cuda.devices": ",".join(d.device_id for d in allocated_devices),
            },
            extra_gids=[
                self._get_video_gid(),
            ],
        )

    async def post_create(self) -> None:
        """Called after workload is created."""
        pass

    async def pre_terminate(self) -> None:
        """Called before workload termination."""
        pass

    async def post_terminate(self) -> None:
        """Called after workload is terminated."""
        await self.ctx.host_services.notify_workload_ended()

    def _get_video_gid(self) -> int:
        """Get the video group ID for GPU access."""
        return grp.getgrnam("video").gr_gid


# =============================================================================
# Agent Runtime Usage Examples
# =============================================================================


async def init_node_plugins() -> dict[str, AbstractDeviceHostPlugin]:
    """
    Initialize node-level plugins (once per node).
    Called during agent runtime startup before any agent instances are created.
    """
    nvidia_host_plugin = NvidiaDeviceHostPlugin()
    await nvidia_host_plugin.init()
    return {"nvidia": nvidia_host_plugin}


async def compute_auto_split_partitions(
    host_plugins: dict[str, AbstractDeviceHostPlugin],
    num_agents: int,
) -> list[frozenset[DeviceId]]:
    """
    Compute device partitions for AUTO_SPLIT mode.
    Uses topology-aware partitioning when available to ensure that
    fabric manager constraints can be satisfied within agent boundaries.
    """
    nvidia_host = host_plugins["nvidia"]

    # Try topology-aware partitioning first
    recommended = await nvidia_host.get_recommended_partitions(num_agents)
    if recommended is not None:
        log.info("Using topology-aware partitioning for %d agents", num_agents)
        return recommended

    # Fallback to naive partitioning
    log.info("Topology-aware partitioning not available, using naive split")
    all_devices = await nvidia_host.list_devices()
    device_ids = [d.device_id for d in all_devices]

    # Simple divmod distribution
    partitions: list[set[DeviceId]] = [set() for _ in range(num_agents)]
    for idx, device_id in enumerate(device_ids):
        partitions[idx % num_agents].add(device_id)

    # Validate and warn if partitions are suboptimal
    for i, partition in enumerate(partitions):
        validation = nvidia_host.validate_partition(frozenset(partition))
        if not validation.is_optimal:
            for warning in validation.warnings:
                log.warning("Agent %d partition: %s", i, warning)

    return [frozenset(p) for p in partitions]


async def init_agent(
    host_plugins: dict[str, AbstractDeviceHostPlugin],
    agent_config: AgentConfig,
    partitions: list[frozenset[DeviceId]] | None,
) -> dict[str, AbstractDevicePlugin]:
    """
    Initialize agent-scoped plugins (per agent instance).

    Args:
        host_plugins: Node-level plugins from init_node_plugins()
        agent_config: Configuration for this agent instance
        partitions: Precomputed partitions from AUTO_SPLIT, or None for MANUAL mode
    """
    nvidia_host = host_plugins["nvidia"]

    # Determine device mask based on partition mode
    if agent_config.partition_mode == PartitionMode.MANUAL:
        # MANUAL mode: use explicit configuration
        device_mask = frozenset(agent_config.device_mask)
    else:
        # AUTO_SPLIT mode: use precomputed partition
        device_mask = partitions[agent_config.agent_index]

    # Validate the partition
    validation = nvidia_host.validate_partition(device_mask)
    if not validation.is_optimal:
        for warning in validation.warnings:
            log.warning("Agent %s: %s", agent_config.agent_id, warning)

    # Create agent-scoped plugin
    nvidia_plugin = nvidia_host.create_agent_context(device_mask)
    await nvidia_plugin.init(agent_config.agent_id)

    return {"nvidia": nvidia_plugin}


async def create_workload(
    agent_plugins: dict[str, AbstractDevicePlugin],
    workload: Workload,
    allocations: dict[str, DeviceAllocation],
) -> Container:
    """
    Create a workload with GPU allocation.
    Demonstrates lifecycle hook usage with fabric manager integration.
    """
    nvidia_plugin = agent_plugins["nvidia"]
    nvidia_alloc = allocations["nvidia"]

    # Create lifecycle hook with scoped context
    hook = await nvidia_plugin.create_lifecycle_hook(workload, nvidia_alloc)

    # Get workload configuration (this integrates with fabric manager)
    config = await hook.pre_create()

    # Merge config into container/process creation params
    container = await create_container(workload, config)

    # Notify hook that creation is complete
    await hook.post_create()

    return container


async def terminate_workload(
    hook: NvidiaLifecycleHook,
    container: Container,
) -> None:
    """
    Terminate a workload and clean up GPU resources.
    """
    # Pre-termination hook (optional cleanup)
    await hook.pre_terminate()

    # Terminate the container
    await container.stop()

    # Post-termination hook (notify fabric manager)
    await hook.post_terminate()
