---
Author: Joongi Kim (joongi@lablup.com)
Status: Draft
Created: 2025-11-28
Created-Version: "25.15"
Target-Version: "26.2"
Implemented-Version:
---

# Accelerator Interface v2

## Current Design

### `AbstractComputePlugin` API

| Function                                                         | Role                                                                                                                                   |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `list_devices()`                                                 | List the available devices in the node                                                                                                 |
| `available_slots()`                                              | List the currently available resource slot types as configured                                                                         |
| `get_metadata()`                                                 | Return the resource slot display metadata (human readable naming, etc.)                                                                |
| `extra_info()`                                                   | Return driver / compute API versions                                                                                                   |
| `get_node_hwinfo()`                                              | Return the node's hardware-specific information as an arbitrary key-value map                                                          |
| `create_alloc_map()`                                             | Create an `AbstractAllocMap` which may be provided by either the Backend.AI agent (discrete / fractional) or the plugin, as configured |
| `get_hooks(distro, arch)`                                        | Get additional host files to mount as library hooks depending on the given container image base distro information                     |
| `generate_docker_args(docker, device_alloc)`                     | Generate a nested dict to merge with the Docker container creation API params                                                          |
| `get_attached_devices(device_alloc)`                             | Extract the list of devices used in the given allocation, with their metadata                                                          |
| `get_docker_networks(device_alloc)`                              | Generate a list of Docker networks to attach depending on the given allocation                                                         |
| `generate_mounts(source_path, device_alloc)`                     | Generate additiona host files to mount                                                                                                 |
| `generate_resource_data(device_alloc)`                           | Generate a list of strings (in KEY=VALUE form) to put into `resource.txt` in the container                                             |
| `restore_from_container(container, alloc_map)`                   | Reconstruct the device allocation from the `aiodocker.DockerContainer` object                                                          |
| `gather_{node,container,process}_metrics(stat_ctx[, target_id])` | Collects the raw metric values such as processor and memory utilization per node, container, or process                                |

### `AbstractComputeDevice` Struct

See [BEP-1000](https://github.com/lablup/beps/blob/main/proposals/BEP-1000-redefining-accelerator-metadata.md) for the new proposal and its comparison with the current design.

## Proposed Design

### Class Decomposition Overview

The following diagram shows how the monolithic `AbstractComputePlugin` is decomposed into purpose-specific classes in the new design:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CURRENT DESIGN                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                        AbstractComputePlugin                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Node-level APIs:                                                        │  │  │
│  │  │   list_devices(), get_metadata(), extra_info(), get_node_hwinfo(),      │  │  │
│  │  │   gather_node_metrics()                                                 │  │  │
│  │  ├─────────────────────────────────────────────────────────────────────────┤  │  │
│  │  │ Agent-level APIs:                                                       │  │  │
│  │  │   available_slots(), create_alloc_map(), get_attached_devices(),        │  │  │
│  │  │   gather_container_metrics(), gather_process_metrics()                  │  │  │
│  │  ├─────────────────────────────────────────────────────────────────────────┤  │  │
│  │  │ Docker-specific APIs (workload config generation):                      │  │  │
│  │  │   get_hooks(), generate_docker_args(), get_docker_networks(),           │  │  │
│  │  │   generate_mounts(), generate_resource_data(), restore_from_container() │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│  ┌─────────────────────────────┐                                                    │
│  │   AbstractComputeDevice     │   Device metadata struct                           │
│  └─────────────────────────────┘                                                    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                        │
                                        │ Decomposition
                                        ▼

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PROPOSED DESIGN                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                    AbstractDeviceHostPlugin (Node-level)                      │  │
│  │    list_devices(), configurable_slots(), get_node_info(),                     │  │
│  │    gather_node_metrics(), create_agent_context()                              │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│         │                                                                           │
│         │ creates (with device_mask)                                                │
│         ▼                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                     AbstractDevicePlugin (Agent-level)                        │  │
│  │    list_devices(), available_slots(), create_alloc_map(),                     │  │
│  │    alloc_to_devices(), gather_workload_metrics(), gather_process_metrics(),   │  │
│  │    create_lifecycle_hook()                                                    │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│         │                                                                           │
│         │ creates (per workload)                                                    │
│         ▼                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                     AbstractLifecycleHook (Workload-level)                    │  │
│  │    pre_create() → WorkloadConfig, post_create(),                              │  │
│  │    pre_terminate(), post_terminate()                                          │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│  ┌─────────────────────────────┐  ┌──────────────┐  ┌───────────────────────────┐   │
│  │      AbstractDevice         │  │   Workload   │  │     WorkloadConfig        │   │
│  │  (formerly ComputeDevice)   │  │    Struct    │  │        Struct             │   │
│  └─────────────────────────────┘  └──────────────┘  └───────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Key changes:**
- **Node vs Agent separation**: APIs that operate on the entire node are now in `AbstractDeviceHostPlugin`, while agent-scoped APIs are in `AbstractDevicePlugin`
- **Device masking**: Each `AbstractDevicePlugin` instance only sees its assigned subset of devices
- **Lifecycle hooks**: Docker-specific methods are replaced by a generic `AbstractLifecycleHook` that returns backend-agnostic `WorkloadConfig`
- **Cleaner struct naming**: `AbstractComputeDevice` → `AbstractDevice`

### Key Goals

* Make it applicable to non-Docker agent backends
    - Many existing plugin APIs are highly coupled with Docker-specific terminology and API parameter formats
* Allow programmatic extension of container lifecycle events
    - e.g., Interact with a vendor-provided device management service when creating or destroying new containers in a node
* Tidy up redundant and messy methods that only expose partial information
* Provide more detailed accelerator metadata ([BEP-1000](https://github.com/lablup/beps/blob/main/proposals/BEP-1000-redefining-accelerator-metadata.md))
* Support multi-agent deployments on a single compute node ✨
    - A single physical node may host multiple agent instances
    - Each agent instance should only access a subset of devices (allow list)
    - Clearly separate node-level APIs from agent-level APIs

### Multi-Agent Architecture Overview ✨

In a multi-agent deployment, a single physical compute node hosts multiple Backend.AI agent instances. The agent runtime initializes once per node and manages the global view of all devices, while each agent instance operates with a partitioned subset of devices.
(NOTE: partioning here means per-device, *not* within-device!)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Compute Node (Physical Host)                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Agent Runtime (Node-level)                   │  │
│  │  - Global device discovery                                │  │
│  │  - Node-level metrics collection                          │  │
│  │  - Device partitioning & allocation                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│  │   Agent 1   │      │   Agent 2   │      │   Agent N   │      │
│  │ (GPU 0, 1)  │      │ (GPU 2, 3)  │      │ (GPU N..M)  │      │
│  │  Workloads  │      │  Workloads  │      │  Workloads  │      │
│  └─────────────┘      └─────────────┘      └─────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### `AbstractDeviceHostPlugin` API (Node-level) ♻️

These APIs are called once per node during the agent runtime initialization. They provide the global view of all available devices before partitioning.

| Function                               | Role                                                                                               |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `list_devices()`                       | List all available devices in the node (global view)                                               |
| `configurable_slots()` ✨              | List all possible resource slot types along with display metadata                                  |
| `get_node_info()` ♻                    | Get the node information such as driver/runtime versions and hardware info using a structured dataclass |
| `gather_node_metrics(stat_ctx)` ♻      | Collect node-level metrics such as total processor and memory utilization across all devices       |
| `create_agent_context(device_mask)` ✨ | Create an `AbstractDevicePlugin` instance scoped to the specified device subset                    |
| `get_device_topology()` ✨             | Return the device interconnect topology (e.g., NVLink/NVSwitch connections) as a structured object |
| `get_host_service_client(service_name)` ✨ | Return a client interface for host-level services (e.g., nvidia-fabric-manager)                |
| `get_recommended_partitions(num_agents)` ✨ | Return topology-aware partition recommendations that respect hardware domain boundaries (e.g., NVSwitch groups) |
| `validate_partition(device_ids)` ✨    | Validate if a partition respects hardware topology; returns warnings if it splits hardware domains |

### `AbstractDevicePlugin` API (Agent-level) ✨

Each agent instance creates its own `AbstractDevicePlugin` with a `device_mask` that acts as an allow list. This context provides agent-scoped operations that only see and manage the devices included in the mask.

| Function                                                    | Role                                                                                                |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `__init__(plugin, device_mask)`                             | Initialize with the parent plugin and the set of allowed device IDs                                 |
| `list_devices()`                                            | List only the devices assigned to this agent (filtered by device_mask)                              |
| `available_slots()`                                         | List the currently allocatable resource slot types within this agent's partition                    |
| `create_alloc_map()`                                        | Create an `AbstractAllocMap` instance with device_mask applied                                      |
| `create_lifecycle_hook(workload, device_alloc)` ✨          | Create an `AbstractLifecycleHook` instance with a scoped `LifecycleHookContext`                     |
| `alloc_to_devices(device_alloc)` ♻️                         | Extract the list of devices used in the given allocation, with their metadata                       |
| `gather_workload_metrics(stat_ctx, workload_id)` ♻          | Collect metrics for a specific workload (container or process tree) managed by this agent           |
| `gather_process_metrics(stat_ctx, pid)` ♻                   | Collect metrics for a specific process within a workload                                            |

#### Struct ✨

| Attribute       | Content                                                                              |
| --------------- | ------------------------------------------------------------------------------------ |
| `host_plugin`   | Reference to the parent `AbstractDeviceHostPlugin` instance                             |
| `device_mask`   | Frozen set of `DeviceId` values (allow list) that this agent can access              |
| `agent_id`      | The unique identifier of the agent instance                                          |
| `devices`       | Cached list of `AbstractDevice` filtered by `device_mask`                     |
| `alloc_map`     | The `AbstractAllocMap` instance scoped to this agent's devices                       |

The `AbstractDevicePlugin` acts as a facade that provides an agent-scoped view of the compute plugin. It ensures that all operations respect the device partitioning configured for the agent.

Here the "workload" means either a container or a (native) process tree, depending on the agent backend implementation.

### Device Masking and Partitioning ✨

The `device_mask` is a set of `DeviceId` values that acts as an **allow list** defining which devices an agent instance can access. Only devices included in the mask are visible and allocatable to the agent. This enables:

* **Resource Isolation**: Each agent only sees its assigned devices, preventing cross-agent resource conflicts
* **Allocation Modes**:
    - `AUTO_SPLIT`: Devices are automatically divided among agents
    - `MANUAL`: Explicit device assignment per agent via configuration
    - Note: Devices are always mutually exclusive between agents. Cross-agent device sharing is not supported.

When `AbstractDevicePlugin` is created with a `device_mask`:
1. `list_devices()` returns only devices in the mask
2. `available_slots()` reflects only the capacity of masked devices
3. `create_alloc_map()` creates an allocation map that enforces the mask
4. Allocation requests for devices outside the mask are rejected

#### AUTO_SPLIT Mode

In `AUTO_SPLIT` mode, the agent runtime automatically partitions devices among agent instances. The partitioning strategy depends on whether topology information is available:

**Topology-aware partitioning (recommended):**

When the plugin provides `get_recommended_partitions()`, the agent runtime uses topology-aware partitioning that respects hardware domain boundaries (e.g., NVSwitch groups). This ensures that fabric manager constraints can always be satisfied within a single agent's device_mask.

```
Example: 8 GPUs with NVSwitch groups {0,1,4,5} and {2,3,6,7}, 2 agents

Naive split:     Agent 0 = [0,1,2,3], Agent 1 = [4,5,6,7]
                 → Each agent spans TWO NVSwitch groups (suboptimal)

Topology-aware:  Agent 0 = [0,1,4,5], Agent 1 = [2,3,6,7]
                 → Each agent owns ONE complete NVSwitch group (optimal)
```

**Fallback partitioning:**

When topology information is unavailable or `get_recommended_partitions()` returns `None`, the runtime falls back to simple `divmod(total_devices, num_agents)` distribution:

* Example: 5 GPUs with 2 agents → Agent 0 gets devices [0, 1, 2], Agent 1 gets devices [3, 4]
* Example: 8 GPUs with 3 agents → Agent 0 gets [0, 1, 2], Agent 1 gets [3, 4, 5], Agent 2 gets [6, 7]

The agent runtime constructs `device_mask` for each agent and passes it to `create_agent_context()`. When using topology-aware partitioning, the runtime also calls `validate_partition()` to log warnings if the resulting partition is suboptimal.

#### MANUAL Mode

In `MANUAL` mode, administrators explicitly configure device assignments per agent:

```toml
[[agents]]
[agents.agent]
id = "agent-1"
[agents.resource]
device_mask = ["GPU-0", "GPU-1"]

[[agents]]
[agents.agent]
id = "agent-2"
[agents.resource]
device_mask = ["GPU-2", "GPU-3"]
```

The agent runtime validates that:
- All specified device IDs exist in the node
- No device ID appears in multiple agents' masks
- The union of all masks covers the intended devices

> **Note**: The `device_mask` operates strictly as an allow list. Excluding specific devices (e.g., faulty devices) is handled separately by the multi-agent runtime configuration, outside the scope of this plugin interface.

### `AbstractDevice` Struct (formerly `AbstractComputeDevice`)

See [BEP-1000](https://github.com/lablup/beps/blob/main/proposals/BEP-1000-redefining-accelerator-metadata.md) for the new proposal.

### `AbstractLifecycleHook` API ✨

| Function                        | Role                                                                                                                                                                 |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__(context)`             | Initialize the instance with a `LifecycleHookContext` providing scoped access to workload info, allocated devices, topology view, and host services                 |
| `pre_create()`                  | Invoked before workload is created.<br>It may deny or (temporarily) fail the creation by raising predefined exceptions.<br>Should return a `WorkloadConfig` struct. |
| `post_create()`                 | Invoked after workload is created.                                                                                                                                   |
| `pre_terminate()`               | Invoked before workload is terminated.<br>It cannot cancel the termination but may defer termination for plugin-specific cleanup.                                    |
| `post_terminate()`              | Invoked after workload is terminated.                                                                                                                                |

This new API merges and replaces Docker-specific argument/mount generation methods in the prior design.

`AbstractLifecycleHook` should be designed as stateless, and it should be able to restore additional state from the container if necessary, to ensure that the Backend.AI Agent is fully restartable at any time.

### `LifecycleHookContext` Struct ✨

The `LifecycleHookContext` provides controlled, scoped access to host services, ensuring lifecycle hooks cannot affect other agents' workloads or access devices outside their allocation.

| Attribute           | Content                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------ |
| `workload`          | The `Workload` struct for the current workload                                                   |
| `device_alloc`      | The `DeviceAllocation` for this workload                                                         |
| `agent_id`          | The unique identifier of the agent instance                                                      |
| `allocated_devices` | Tuple of `AbstractDevice` instances allocated to this workload (read-only)                       |
| `topology_view`     | `ScopedTopologyView` providing topology info filtered to allocated devices only                  |
| `host_services`     | `ScopedHostServices` providing host service access restricted to the workload's allocated devices |

**Security guarantees:**
- Hooks cannot access devices outside their allocation
- Hooks cannot affect other agents' workloads through host service manipulation
- All host service calls are scoped to the workload's allocated devices and include workload ID for audit tracking

### `Workload` Struct ✨

| Attribute | Content                                            |
| --------- | -------------------------------------------------- |
| `id`      | The identifier (container ID or leader process ID) |
| `type`    | "container" \| "process_tree"                      |

### `WorkloadConfig` Struct ✨

| Attribute        | Content                                                                                                                                |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `mounts`         | List of host-to-workload mounts, including device files and library hooks                                                              |
| `env_vars`       | Key-value map of environment variables                                                                                                 |
| `resource_data`  | Key-value map appended to `resource.txt` readable in the workload                                                                      |
| `networks`       | List of network names to attach for plugin (only applicable when the network namespace is isolated)                                    |
| `extra_gids`     | List of Linux GIDs applied to the workload                                                                                             |
| `extra_syscalls` | List of Linux syscalls additionally allowed in the workload (only applicable when there is a syscall filter, like AppArmor or Seccomp) |

All fields are optional.

### Example: NVIDIA GPU Plugin with Fabric Manager Integration

The following pseudocode demonstrates how the proposed APIs would be implemented for NVIDIA GPUs, including integration with nvidia-fabric-manager for NVSwitch topology management.

📄 **Full example code**: [BEP-1016/nvidia_plugin_example.py](BEP-1016/nvidia_plugin_example.py)

The example includes:

| Component | Description |
|-----------|-------------|
| `NvidiaFabricManagerClient` | Client for interacting with nvidia-fabric-manager service |
| `NvidiaDeviceHostPlugin` | Node-level plugin with topology discovery and partition recommendations |
| `NvidiaDevicePlugin` | Agent-scoped plugin with device masking |
| `LifecycleHookContext` | Scoped context providing controlled access to host services |
| `ScopedTopologyView` | Topology view filtered to allocated devices |
| `ScopedHostServices` | Host service access restricted to workload's devices |
| `NvidiaLifecycleHook` | Workload lifecycle hook with fabric manager integration |
| Agent runtime functions | `init_node_plugins()`, `compute_auto_split_partitions()`, `init_agent()`, `create_workload()` |

Key patterns demonstrated:

1. **Topology-aware partitioning**: `get_recommended_partitions()` returns partitions aligned with NVSwitch group boundaries
2. **Scoped access**: `LifecycleHookContext` prevents hooks from accessing devices outside their allocation
3. **Fabric manager integration**: Hooks configure NVLink routing and notify workload lifecycle events
4. **Security guarantees**: All host service calls are scoped to allocated devices with workload ID for audit tracking

### Discussion

* How to handle & distinguish in-place restarts and relocated restarts in lifecycle hooks?
* Would it better to provide a managed state-store interface to the lifecycle hook instances instead of requiring them to be stateless?
* A better naming for "workload"?
    - Just keep using "kernel" in align with the cluster-wide scheduler?
    - Need to consider the relationship with "session" as well...

#### Multi-Agent Specific Discussions ✨

* **Device Mask Immutability**: Should `device_mask` be immutable after `AbstractDevicePlugin` creation, or should it support dynamic reconfiguration?
    - Immutable: Simpler implementation, but requires agent restart for repartitioning
    - Mutable: More flexible, but adds complexity for handling in-flight workloads during reconfiguration

* **Cross-Agent Device Sharing**:
    - **Decision**: Cross-agent device sharing is not supported. Devices are always mutually exclusive between agents within a node. This simplifies the implementation and avoids coordination complexity at the plugin level.

* **Lifecycle Hook Scope**: Should `AbstractLifecycleHook` be aware of multi-agent context?
    - Current design: Hooks are scoped to a single agent's workloads
    - Alternative: Node-level hooks that can observe all agents' workloads (e.g., for vendor-specific device manager integration)

* **Host Service Integration**: Lifecycle hooks may need to interact with host-level services such as nvidia-fabric-manager for NVSwitch/NVLink configuration:
    - **Proposed solution**: Use `LifecycleHookContext` with scoped access instead of direct `host_plugin` reference
    - `ScopedTopologyView`: Provides topology information filtered to allocated devices only
    - `ScopedHostServices`: Provides host service access restricted to the workload's allocated devices
    - This ensures hooks cannot affect other agents' workloads or access devices outside their allocation
    - Trade-off: Slightly more complex API surface, but provides strong isolation guarantees

* **Topology-aware Device Partitioning**: When device interconnect topology (e.g., NVSwitch groups) exists, how should multi-agent partitioning consider it?
    - **Recommendation**: Partition devices along hardware domain boundaries (e.g., NVSwitch groups) to ensure fabric manager constraints can always be satisfied within a single agent's `device_mask`
    - `get_recommended_partitions(num_agents)` API provides topology-aware partition suggestions
    - `validate_partition(device_ids)` API warns if a partition splits hardware domains
    - AUTO_SPLIT mode should prefer topology-aware partitioning when available
    - **Trade-off**: Reduces partitioning flexibility but guarantees that topology-aware allocation never requires cross-agent coordination
    - **Implication**: Fabric manager's allocation adjustment suggestions are guaranteed to stay within agent boundaries

* **Metrics Aggregation**: How should node-level metrics relate to agent-level metrics?
    - Option A: Node-level metrics are independently collected (may differ from sum of agent metrics)
    - Option B: Node-level metrics are computed as aggregation of agent-level metrics
    - Need to consider overhead and accuracy tradeoffs

* **Agent Context Lifecycle**: When an agent instance terminates (gracefully or due to crash), how should the `AbstractDevicePlugin` handle cleanup?
    - Should there be a `close()` or `cleanup()` method on `AbstractDevicePlugin`?
    - How to handle orphaned workloads when an agent crashes?
