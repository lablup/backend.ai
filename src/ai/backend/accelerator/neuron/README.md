# Backend.AI Accelerator Plugin for AWS Neuron

Adds support for AWS Neuron accelerators — AWS Trainium (`trn1`, `trn1n`, `trn2`)
and AWS Inferentia (`inf1`, `inf2`) — to the Backend.AI agent.

Package name: `backend.ai-accelerator-neuron`
Entry point: `backendai_accelerator_v21` → `neuron`

## The allocation unit is the NeuronCore, not the Neuron device

The plugin reports a single slot, **`neuron.core`** (`SlotTypes.COUNT`). One
Neuron device carries `nc_count` NeuronCores (2 on Trainium1), and the plugin
emits one compute device per core.

This is the one design decision in the plugin that cannot be reversed without a
data migration, because the slot name becomes a primary key in
`resource_slot_types` and is referenced by `agent_resources` and
`resource_allocations`. Three independent pieces of evidence point at the core:

1. **AWS's own allocation primitive is the core.** `NEURON_RT_VISIBLE_CORES` is
   the supported way to confine a process to a subset of the hardware, and
   `NEURON_RT_NUM_CORES` is explicitly deprecated in its favour.
2. **Every runtime-varying metric is keyed per core.** In sysfs the device level
   exposes only static capacity plus driver-owned host memory, while
   `memory_usage`, `status` and `other_info` counters all live under
   `neuron_core{N}/`.
3. **sysfs models cores as first-class objects**, as real nested directories
   under each `neuron{N}` device.

Device identity (`bdf`, `serial_number`, the `neuron{N}` index) is kept as
metadata on each core device rather than as the allocation key. Core-granular
slots aggregate upward to whole devices for free; device-granular slots could
never be subdivided later.

A core's `device_id` is its **logical NeuronCore index** as reported by
`neuron-ls` (`neuroncore_ids`), which is exactly the integer
`NEURON_RT_VISIBLE_CORES` accepts.

## Host requirements

* `aws-neuronx-dkms` driver, exposing `/dev/neuron0..N` (mode `0666`, so no
  supplementary group is needed) and
  `/sys/devices/virtual/neuron_device/neuron*/`.
* `aws-neuronx-tools`, providing `neuron-ls`.

`neuron-ls` is looked up at `/opt/aws/neuron/bin/neuron-ls` first and only then
on `$PATH`. That directory is put on `PATH` by the DLAMI profile scripts, so
under systemd or a container entrypoint the bare name is not resolvable.

If the tool or the driver is missing, the plugin logs the reason and sets
`enabled = False`; it never raises out of `init()`.

## Discovery

Discovery shells out to `neuron-ls --json-output`, whose output is a top-level
JSON **array**:

```json
[{"neuron_device": 0, "bdf": "0000:00:1e.0", "cpu_affinity": "0-7",
  "numa_node": "-1", "connected_to": null, "nc_count": 2,
  "memory_size": 34359738368, "neuroncore_ids": [0, 1], "neuron_processes": []}]
```

Note the shapes: `neuron_device` is an `int` but `numa_node` is a **string**,
`connected_to` is `null` on single-device instances, and `memory_size` is in
**bare bytes** (not a human-readable string). A `numa_node` of `-1` is clamped
to node 0. `memory_size` is divided by `nc_count` for each core's
`memory_size`, since the cores of one device share that HBM pool.

## Metrics

`gather_node_measures` reads per-core counters from sysfs on each stat tick:

| Metric | Source |
| --- | --- |
| `neuron_mem` | `neuron_core*/stats/memory_usage/device_mem/present`, against the per-core share of the device capacity |
| `neuron_host_mem` | `neuron_core*/stats/memory_usage/host_mem/present` |

The `total` leaves in sysfs are cumulative allocation counters rather than
capacity (they read 0 on an idle core), so capacity comes from `neuron-ls`.

`neuron-monitor` is deliberately **not** used. It is a streaming collector with
no one-shot mode, so consuming it would mean running a persistent vendor daemon
inside the agent, which no other accelerator plugin does, whereas
`gather_node_measures` is a per-tick pull. As a consequence, per-core
*utilization* — which needs `neuron-monitor` plus an attached process — is not
reported in this version.

## Container plumbing

`generate_docker_args` returns:

* `HostConfig.Devices` mapping each allocated `/dev/neuron{N}` to
  `/dev/neuron{alloc_idx}`, with `CgroupPermissions: "rwm"`, renumbered so the
  container always sees `0..k-1`. Missing device nodes are skipped rather than
  failing container creation.
* `CapAdd: ["IPC_LOCK"]`, `IpcMode: "host"` and an unlimited `memlock` ulimit,
  which the Neuron runtime needs for its large pinned-memory registration.
* `Env: ["NEURON_RT_VISIBLE_CORES=..."]`, holding the **container-local** core
  indices of the allocated cores.

A device node carries *all* of that device's cores, so allocating a subset of
the cores of a device still mounts the whole device node — the container can see
sibling cores it was not allocated. `NEURON_RT_VISIBLE_CORES` is what confines
the runtime to the allocated cores.

## Configuration

Optional keys under the plugin's own config section:

| Key | Meaning |
| --- | --- |
| `neuron_ls_path` | Absolute path to `neuron-ls`, overriding the default lookup |
| `device_mask` | Comma-separated NeuronCore ids to hide from Backend.AI |
