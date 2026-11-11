---
Author: Joongi Kim (joongi@lablup.com)
Status: Draft
Created: 2026-11-11
Created-Version: 26.10.0
Target-Version:
Implemented-Version:
---

# Accelerator Plugin Container Lifecycle Hooks

## Related Issues

- JIRA: not created yet
- Consumer: the fractional allocation mode of `backend.ai-accelerator-cuda-open`, the standalone CUDA plugin
- Upstream: [BEP-1016](BEP-1016-accelerator-interface-v2.md) (Accelerator Interface v2, `AbstractLifecycleHook`)

## Goal

An accelerator plugin shapes a container only before the container exists (`generate_docker_args`, `generate_mounts`, `generate_resource_data`). It cannot act on the container itself. This BEP adds two Agent calls that let a plugin act on a created container before it starts and release per-container state when it goes away, and fixes two core defects found while building the first consumer.

The first consumer is the fractional mode of the standalone CUDA plugin. It provides GPU memory as the `cuda.mem` slot (bytes) on shared GPUs, with no `LD_PRELOAD` hook in the container:

| What the plugin enforces | How | Needs from the core |
|---|---|---|
| GPU memory limit per container | `nvmlDeviceSetMemoryLimits_v1` on the container's cgroup, accounted by the cgroup v2 `dmem` controller (Linux 6.14+) or `misc` (Linux 5.14+), driver r615+ | The container ID after create and before start, so the limit is in place before the first process runs |
| SM share per container | One MPS namespace (and SM partition) per container | A call when the container is gone, to delete the namespace and partitions |
| Restored allocations after an Agent restart | `restore_from_container()` reads `resource.txt` | Exact byte counts for bytes-type slots |
| agent heartbeat | The Agent reports `cuda.mem` capacity | A `resource_slot_types` row for `cuda.mem` |

## Non-goals

- The BEP-1016 v2 plugin interface (`AbstractLifecycleHook`, `Workload`, `WorkloadConfig`)
- Agent backends other than Docker.
- Config changes returned by a hook. Container config stays in `generate_docker_args`.
- The follow-up items in the open questions: MIG slot type registration, the GPU count hint, the in-tree `cuda_open` copy.

## Current design and scope, by area

### Accelerator plugin interface (`AbstractComputePlugin`)

| | Item |
|---|---|
| ✅ exists | `generate_docker_args`, `generate_mounts`, `generate_resource_data`, `restore_from_container`, all called before create or at restore |
| ➕ to add | `on_container_created(container_id, device_alloc)`, `on_container_destroyed(container_id, device_alloc)`, both with no-op defaults |

### Docker Agent

| | Item |
|---|---|
| ✅ exists | `start_container`: create → record the CID in `resource.txt` → start. A failure after create raises `ContainerCreationError` with the container ID, and the failure handler destroys the kernel by that ID |
| ✅ exists | `clean_kernel`: collect logs → close domain socket proxies → delete the container → leave the networks |
| ➕ to add | Call `on_container_created` per plugin after the CID is recorded and before start |
| ➕ to add | Call `on_container_destroyed` per plugin in `clean_kernel` before the container is deleted |

### `resource.txt`

| | Item |
|---|---|
| ✅ exists | `KernelResourceSpec.write_to_string()` writes a bytes-type slot allocation as a `BinarySize` string (`1.67g`), which rounds it. Reading accepts the `BinarySize` form and plain numbers |
| ➕ to change | Write bytes-type slot allocations as plain byte counts. Reading is unchanged |

### Manager resource slot types

| | Item |
|---|---|
| ✅ exists | `resource_slot_types` rows for `cuda.device` and `cuda.shares`. An agent heartbeat that reports an unregistered slot fails on the `agent_resources` foreign key |
| ➕ to add | An Alembic migration that registers `cuda.mem` (`bytes`) |

## Implementation design

### Hook contract

| Hook | Called | Arguments | On error |
|---|---|---|---|
| `on_container_created` | After `docker create` and after the CID is written to `resource.txt`, before `docker start` | Container ID, the plugin's own `DeviceAllocation` | Aborts the start: raised as `ContainerCreationError`, then the existing failure path destroys and cleans the kernel |
| `on_container_destroyed` | In `clean_kernel`, after the container stopped and its logs were collected, before it is deleted. Also called when `debug.skip_container_deletion` keeps the container | Container ID, the plugin's own `DeviceAllocation` | Logged per plugin with the traceback. The remaining plugins and the cleanup continue |

```python
class AbstractComputePlugin:
    async def on_container_created(
        self, container_id: ContainerId, device_alloc: DeviceAllocation
    ) -> None: ...
    async def on_container_destroyed(
        self, container_id: ContainerId, device_alloc: DeviceAllocation
    ) -> None: ...
```

Flow of one kernel:

```
generate_docker_args → docker create → CID in resource.txt → on_container_created (per plugin) → docker start
container exits → clean_kernel → on_container_destroyed (per plugin) → docker delete → allocations freed
```

Rules a plugin follows:

| Rule | Reason |
|---|---|
| A hook is called once per plugin with an entry in `KernelResourceSpec.allocations`. A plugin without an allocation for the kernel is not called | The allocation is the plugin's only per-kernel input |
| `on_container_destroyed` is idempotent and accepts a container whose `on_container_created` did not run or failed | A failed start, a cancelled create and a restart after an Agent crash all reach `clean_kernel` |
| A hook reads per-container state from the container (labels, `docker inspect`), not from plugin memory | The Agent restarts at any time; BEP-1016 states the same for `AbstractLifecycleHook` |
| A kernel restart runs both hooks again | A restart is destroy → clean → create of a new container |

### Exact bytes in `resource.txt`

`write_to_string()` writes each bytes-type per-device allocation as an integer (`cuda.mem=0:4294967296`). The rounded `BinarySize` string made an allocation restored by `restore_from_container()` differ from the amount the plugin enforced, and the alloc map drifted after an Agent restart. Reading still accepts both forms, so a kernel started by an older Agent restores as before.

### `cuda.mem` slot type

| Column | Value |
|---|---|
| `slot_name` | `cuda.mem` |
| `slot_type` | `bytes` |
| `display_name` | `GPU Memory` |
| `display_unit` | `GiB` |
| `number_format` | `{"binary": true, "round_length": 1}` |
| `rank` | 450 |

The upgrade writes the row under a fixed uuid with `ON CONFLICT DO NOTHING`, then the graph node and its edges that `ResourceSlotTypeUpserter` writes: the node owns and governs itself, and the `global` and `public` scopes own and govern it. A `cuda.mem` an operator already registered keeps its row and gets the node. The downgrade deletes only the row under the fixed uuid, and only when none of the six tables with a foreign key to `slot_name` refers to it. `fixtures/manager/example-resource-slot-types.json` carries the same row, since a fresh install (`mgr schema oneshot`) stamps the head without running the migration.

### Use by the CUDA plugin

For reference, not part of the core change.

| Hook | Fractional mode |
|---|---|
| `on_container_created` | Create the container's cgroup ahead of the engine with `dmem` or `misc` delegated to it, check the leaf has the controller, set the hard limit per GPU through NVML, mark the container's MPS namespace attached |
| `on_container_destroyed` | Delete the MPS namespace and its SM partitions, clear the limit, remove the cgroup if the engine left it |

The device mode does nothing in either hook.

## Migration / Compatibility

| Change | Effect |
|---|---|
| Two hooks with no-op defaults | Additive. Existing accelerator plugins and the mock accelerator are unaffected |
| Bytes written as integers | An older Agent reads the new form (`BinarySize.from_str` accepts plain numbers). A newer Agent reads the old form |
| `cuda.mem` migration | Idempotent. Without it, a fractional-mode Agent's agent heartbeat fails until an operator registers the slot type by hand |
| MIG slot names of the standalone plugin | `cuda.device:<profile>` (`cuda.device:1g.10gb`, `cuda.device:2g.48gb+gfx`), with no `-mig` suffix. The core does not parse the suffix; each name needs its own `resource_slot_types` row (see the open questions) |

## Implementation Plan

1. Core, branch `topic/compute-plugin-container-hooks`: the two hooks, exact bytes, `cuda.mem`, unit tests
2. Core follow-ups from the open questions, one PR each.
3. BEP-1016: replace the two methods with `AbstractLifecycleHook.post_create()` and `post_terminate()`.

## Decision Summary

| Decision | Rationale |
|---|---|
| Two methods on `AbstractComputePlugin` now, not the BEP-1016 interface | Additive and small. `on_container_created` maps to `post_create()`, `on_container_destroyed` to `post_terminate()` |
| `on_container_created` runs between create and start | The cgroup limit and MPS binding must exist before the first process. After start, a process can allocate GPU memory before the limit is set |
| A failure in `on_container_created` aborts the start | A container without its limit must not run |
| A failure in `on_container_destroyed` is only logged | Cleanup of one plugin must not block deleting the container and freeing the allocations |
| `on_container_destroyed` runs before the container is deleted | The plugin still reads the container's labels and cgroup parent |
| A hook gets the container ID and its own allocation only | The plugin inspects the container itself; the interface stays small |
| Enforcement through the driver, cgroups and MPS, no `LD_PRELOAD` | No interposition inside the container image |
| Bytes-type allocations written as integers | The `BinarySize` string rounds them |

## Open Questions

| Question | Options |
|---|---|
| MIG slot types | Each `cuda.device:<profile>` the plugin reports needs a `resource_slot_types` row. Register unknown slot types reported by an Agent in its agent heartbeat, let a plugin declare its slot types, or document an operator step per profile |
| GPU count hint | `cuda.mem` is placed on one GPU. The plugin's alloc map accepts a GPU count to split a request evenly; nothing passes it. Carry a per-session GPU count from the manager through `KernelResourceSpec` to `allocate()` |
| In-tree `src/ai/backend/accelerator/cuda_open` | It uses the same module path and entry point as the standalone package, and `./py` puts `src/` first, so it shadows the standalone package. Remove it or replace it with the standalone package |
| `KernelResourceSpec.to_json_serializable_dict()` | For a bytes slot it assigns a formatted string to `o["slots"]`, replacing the whole mapping. Fix separately |

## Related documents

- [BEP-1016: Accelerator Interface v2](BEP-1016-accelerator-interface-v2.md)
- [BEP-1000: Redefining Accelerator Metadata](BEP-1000-redefining-accelerator-metadata.md)
- [BEP-1061: Agent Kernel Lifecycle Structuring](BEP-1061-agent-kernel-lifecycle.md)
