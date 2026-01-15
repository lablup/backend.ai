---
Author: Joongi Kim (joongi@lablup.com)
Status: Draft
Created: 2025-11-28
Created-Version:
Target-Version:
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

### `AbstractComputePlugin` API (Node-level) ♻️

These APIs are called once per node during the agent runtime initialization. They provide the global view of all available devices before partitioning.

| Function                               | Role                                                                                               |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `list_devices()`                       | List all available devices in the node (global view)                                               |
| `configurable_slots()` ✨              | List all possible resource slot types along with display metadata                                  |
| `get_node_info()` ♻                    | Get the node information such as driver/runtime versions and hardware info using a structured dataclass |
| `gather_node_metrics(stat_ctx)` ♻      | Collect node-level metrics such as total processor and memory utilization across all devices       |
| `create_agent_context(device_mask)` ✨ | Create an `AbstractAgentContext` instance scoped to the specified device subset                    |

### `AbstractAgentContext` API (Agent-level) ✨

Each agent instance creates its own `AbstractAgentContext` with a device mask (allow list). This context provides agent-scoped operations that only see and manage the partitioned devices.

| Function                                                    | Role                                                                                                |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `__init__(plugin, device_mask)`                             | Initialize with the parent plugin and the set of allowed device IDs                                 |
| `list_devices()`                                            | List only the devices assigned to this agent (filtered by device_mask)                              |
| `available_slots()`                                         | List the currently allocatable resource slot types within this agent's partition                    |
| `create_alloc_map()`                                        | Create an `AbstractAllocMap` instance with device_mask applied                                      |
| `create_lifecycle_hook(workload, device_alloc)` ✨          | Create an `AbstractLifecycleHook` instance for workload management                                  |
| `alloc_to_devices(device_alloc)` ♻️                         | Extract the list of devices used in the given allocation, with their metadata                       |
| `gather_workload_metrics(stat_ctx, workload_id)` ♻          | Collect metrics for a specific workload (container or process tree) managed by this agent           |
| `gather_process_metrics(stat_ctx, pid)` ♻                   | Collect metrics for a specific process within a workload                                            |

Here the "workload" means either a container or a (native) process tree, depending on the agent backend implementation.

### Device Masking and Partitioning ✨

The `device_mask` is a set of `DeviceId` values that defines which devices an agent instance can access. This enables:

* **Resource Isolation**: Each agent only sees its assigned devices, preventing cross-agent resource conflicts
* **Flexible Allocation Modes**:
    - `SHARED`: All agents see all devices (device_mask includes all device IDs)
    - `AUTO_SPLIT`: Devices are automatically divided among agents (e.g., 8 GPUs / 2 agents = 4 GPUs each)
    - `MANUAL`: Explicit device assignment per agent via configuration

When `AbstractAgentContext` is created with a `device_mask`:
1. `list_devices()` returns only devices in the mask
2. `available_slots()` reflects only the capacity of masked devices
3. `create_alloc_map()` creates an allocation map that enforces the mask
4. Allocation requests for devices outside the mask are rejected

### `AbstractComputeDevice` Struct

See [BEP-1000](https://github.com/lablup/beps/blob/main/proposals/BEP-1000-redefining-accelerator-metadata.md) for the new proposal.

### `AbstractAgentContext` Struct ✨

| Attribute       | Content                                                                              |
| --------------- | ------------------------------------------------------------------------------------ |
| `plugin`        | Reference to the parent `AbstractComputePlugin` instance                             |
| `device_mask`   | Frozen set of `DeviceId` values that this agent is allowed to access                 |
| `agent_id`      | The unique identifier of the agent instance                                          |
| `devices`       | Cached list of `AbstractComputeDevice` filtered by `device_mask`                     |
| `alloc_map`     | The `AbstractAllocMap` instance scoped to this agent's devices                       |

The `AbstractAgentContext` acts as a facade that provides an agent-scoped view of the compute plugin. It ensures that all operations respect the device partitioning configured for the agent.

### `AbstractLifecycleHook` API ✨

| Function                           | Role                                                                                                                                                                 |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__(workload, device_alloc)` | Initialize the instance with the given workload and allocation                                                                                                       |
| `pre_create()`                     | Invoked before workload is created.<br>It may deny or (temporarily) fail the creation by raising predefined exceptions.<br>Should return a `WorkloadConfig` struct. |
| `post_create()`                    | Invoked after workload is created.                                                                                                                                  |
| `pre_terminate()`                  | Invoked before workload is terminated.<br>It cannot cancel the termination but may defer termination for plugin-specific cleanup.                                   |
| `post_terminate()`                 | Invoked after workload is terminated.                                                                                                                               |

This new API merges and replaces Docker-specific argument/mount generation methods in the prior design.

`AbstractLifecycleHook` should be designed as stateless, and it should be able to restore additional state from the container if necessary, to ensure that the Backend.AI Agent is fully restartable at any time.

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

### Discussion

* How to handle & distinguish in-place restarts and relocated restarts in lifecycle hooks?
* Would it better to provide a managed state-store interface to the lifecycle hook instances instead of requiring them to be stateless?
* A better naming for "workload"?
    - Just keep using "kernel" in align with the cluster-wide scheduler?
    - Need to consider the relationship with "session" as well...

#### Multi-Agent Specific Discussions ✨

* **Device Mask Immutability**: Should `device_mask` be immutable after `AbstractAgentContext` creation, or should it support dynamic reconfiguration?
    - Immutable: Simpler implementation, but requires agent restart for repartitioning
    - Mutable: More flexible, but adds complexity for handling in-flight workloads during reconfiguration

* **Cross-Agent Device Sharing**: In `SHARED` allocation mode, how should multiple agents coordinate when accessing the same device?
    - Option A: Leave coordination entirely to the cluster scheduler (Manager)
    - Option B: Provide plugin-level locking/coordination primitives
    - Option C: Disallow `SHARED` mode for devices that don't support concurrent access

* **Lifecycle Hook Scope**: Should `AbstractLifecycleHook` be aware of multi-agent context?
    - Current design: Hooks are scoped to a single agent's workloads
    - Alternative: Node-level hooks that can observe all agents' workloads (e.g., for vendor-specific device manager integration)

* **Metrics Aggregation**: How should node-level metrics relate to agent-level metrics?
    - Option A: Node-level metrics are independently collected (may differ from sum of agent metrics)
    - Option B: Node-level metrics are computed as aggregation of agent-level metrics
    - Need to consider overhead and accuracy tradeoffs

* **Agent Context Lifecycle**: When an agent instance terminates (gracefully or due to crash), how should the `AbstractAgentContext` handle cleanup?
    - Should there be a `close()` or `cleanup()` method on `AbstractAgentContext`?
    - How to handle orphaned workloads when an agent crashes?
