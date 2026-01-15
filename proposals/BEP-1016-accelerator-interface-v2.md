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

### `AbstractComputePlugin` API

| Function                                                          | Role                                                                                                                               |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `list_devices()`                                                  | List the available devices in the node                                                                                             |
| `configurable_slots()` ✨                                          | List the all possible resource slot types along with the display metadata                                                          |
| `available_slots()` ✨                                             | List the currently allocatable resource slot types as configured                                                                   |
| `create_alloc_map()`                                              | Create an `AbstractAllocMap` instance as configured                                                                                |
| `create_lifecycle_hook(workload, device_alloc)` ✨                 | Create an `AbstractLifecycleHook` instance                                                                                         |
| `alloc_to_devices(device_alloc)` ♻️                               | Extract the list of devices used in the given allocation, with their metadata                                                      |
| `gather_{node,workload,process}_metrics(stat_ctx[, target_id])` ♻ | Collects the raw metric values such as processor and memory utilization per node, workload (container or process tree), or process |
| `get_node_info()` ♻                                               | Get the node information such as driver/runtime versions and additional hardware info using a structured dataclass                 |

Here the "workload" means either a container or a (native) process tree, depending on the agent backend implementation.

### `AbstractComputeDevice` Struct

See [BEP-1000](https://github.com/lablup/beps/blob/main/proposals/BEP-1000-redefining-accelerator-metadata.md) for the new proposal.

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
