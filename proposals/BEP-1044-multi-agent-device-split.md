---
Author: Hyunhoi Koo (hyunhoi@lablup.com)
Status: Draft
Created: 2026-01-29
Created-Version: 26.1.0
Target-Version:
Implemented-Version:
---

# Multi-Agent Device Split: Slot-Based to Device-Based Allocation

## Related Issues

- JIRA: BA-4143, BA-4144, BA-4145, BA-4146
- GitHub: #8433, #8440, #8447, #8463

## Background: Multi-Agent Resource Allocation Modes

Backend.AI supports running multiple agent processes on a single host, each managing a subset of the machine's compute resources. This is useful for isolating workloads, running different container runtimes, or partitioning resources between different user groups.

The system provides three **allocation modes** that determine how resources are divided among agents:

### SHARED Mode

All agents see and can allocate from the full set of available resources. There is no partitioning - agents compete for resources on a first-come-first-served basis. This is the simplest mode and is suitable when agents handle non-overlapping workloads or when resource contention is managed at a higher level.

### AUTO_SPLIT Mode

The system automatically divides resources among agents. Each agent receives an exclusive subset of devices (for discrete resources like CPU cores and GPUs) or a proportional share (for shared resources like memory). This mode requires no manual configuration beyond specifying the number of agents.

### MANUAL Mode

Administrators explicitly configure which resources each agent can use. This provides fine-grained control over resource assignment, allowing specific devices to be assigned to specific agents based on workload requirements, hardware topology, or organizational policies.

## Motivation

As part of the Accelerator Interface v2 redesign ([BEP-1016](BEP-1016-accelerator-interface-v2.md)), we are moving toward device-centric resource management.

The previous multi-agent resource allocation was incorrectly implemented using a **slot-based** configuration where devices were specified by slot names with decimal fractional values:

```toml
[agent.resource.allocations]
devices = { "cuda.mem" = 0.3, "cuda.shares" = 0.5 }
```

This approach has fundamental problems:

1. **No device exclusivity**: Slot-based allocation divides abstract quantities (e.g., "0.5 of cuda.shares") but cannot enforce that agents use mutually exclusive physical devices. For CPU cores and accelerators, multiple agents must not share the same physical device - slot amounts alone cannot express or enforce this.

2. **Abstraction mismatch**: The actual resource being partitioned is a set of physical devices (cuda0, cuda1, etc.), not slot amounts. Slot names like `cuda.mem` and `cuda.shares` are derived properties - we should configure at the device level and derive slots from that, not the other way around.

Since no production or development systems currently use the multi-agent feature with AUTO_SPLIT or MANUAL modes, we can fix this design without backward compatibility concerns.

## Design Overview

The core insight is that resource allocation should work with **physical devices**, not abstract slot amounts:

1. **Discover devices** - Enumerate actual devices from compute plugins (e.g., `cuda0`, `cuda1`, `cpu0`, `cpu1`)
2. **Assign devices to agents** - Each agent receives a specific set of device IDs
3. **Derive slots from assignments** - Slot amounts are computed from assigned devices, not configured directly

This inverts the previous design where slot amounts were configured and devices were implicitly shared.

## Proposed Design

### Device Discovery: GlobalDeviceInfo

Before partitioning, the system builds a global view of all available devices:

```python
@dataclass
class GlobalDeviceInfo:
    plugin: AbstractComputePlugin
    devices: Sequence[AbstractComputeDevice]
    alloc_map: AbstractAllocMap

    @property
    def device_ids(self) -> Sequence[DeviceId]:
        return [device.device_id for device in self.devices]

type GlobalDeviceMap = Mapping[DeviceName, GlobalDeviceInfo]
```

This separates device discovery (what hardware exists) from device allocation (which agent gets what).

### Partition Types: Discrete vs Shared Resources

Not all resources are partitioned the same way:

- **Discrete resources** (CPU cores, GPUs): Must be exclusively assigned to one agent. Partitioned by device ID.
- **Shared resources** (memory): Can be divided by amount without device-level exclusivity. Partitioned by slot amount.

The design uses a union type to represent both:

```python
@dataclass(frozen=True)
class DevicePartition:
    """For discrete resources - specifies which device IDs this agent owns."""
    device_ids: Sequence[DeviceId]

@dataclass(frozen=True)
class SlotPartition:
    """For shared resources - specifies slot amounts this agent can use."""
    slots: Mapping[SlotName, Decimal]

type Partition = DevicePartition | SlotPartition
type ResourceAssignments = Mapping[AgentId, Mapping[DeviceName, Partition]]
```

### ResourcePartitioner: Generating Assignments

A single `ResourcePartitioner` class generates assignments for all modes:

```python
class ResourcePartitioner:
    _SHARED_DEVICE_NAMES: Final = frozenset({DeviceName("mem")})

    @classmethod
    def generate_shared_assignments(cls, global_devices: GlobalDeviceMap) -> ResourceAssignments:
        """SHARED mode: all agents see all devices."""
        ...

    @classmethod
    def generate_autosplit_assignments(
        cls,
        global_devices: GlobalDeviceMap,
        agent_ids: Sequence[AgentId],
        available_slots: SlotsMap,
    ) -> ResourceAssignments:
        """AUTO_SPLIT mode: automatically distribute devices among agents."""
        ...

    @classmethod
    def generate_manual_assignments(
        cls,
        global_devices: GlobalDeviceMap,
        agent_configs: Sequence[AgentUnifiedConfig],
    ) -> ResourceAssignments:
        """MANUAL mode: read explicit assignments from config."""
        ...
```

For AUTO_SPLIT mode, discrete resources use the **fill-from-front** distribution algorithm:

```python
def _calculate_device_partitions(device_ids, agent_ids) -> Mapping[AgentId, DevicePartition]:
    """
    For N devices across M agents:
    - q, r = divmod(N, M)
    - First r agents get (q + 1) devices
    - Remaining agents get q devices
    - Devices assigned in natural sorted order
    """
```

Example: 5 GPUs across 3 agents → agent-1 gets [cuda0, cuda1], agent-2 gets [cuda2, cuda3], agent-3 gets [cuda4]

Device IDs are sorted using **natural sort** to handle numeric suffixes correctly (e.g., "cuda0", "cuda1", "cuda10" sorts as 0, 1, 10, not lexicographically as 0, 1, 10).

### Configuration: MANUAL Mode

The configuration format changes from slot-based to device-based:

```python
class ResourceAllocationConfig(BaseConfigSchema):
    cpu: Sequence[DeviceId]                        # e.g., ["0", "1", "2", "3"]
    mem: BinarySizeField                           # e.g., "16G"
    devices: Mapping[DeviceName, Sequence[DeviceId]]  # e.g., {"cuda": ["cuda0", "cuda1"]}
```

Note that:
- `cpu` is a separate field because CPU cores are always required
- `mem` uses a human-readable size (e.g., "16G") because memory doesn't have discrete device IDs
- `devices` maps device names to lists of device IDs for accelerators

Example configuration:

```toml
# MANUAL mode configuration
[resource]
allocation-mode = "manual"

[[agents]]
[agents.agent]
id = "agent-1"

[agents.resource]
cpu = ["0", "1", "2", "3"]
mem = "32G"
devices = { cuda = ["cuda0", "cuda1"] }

[[agents]]
[agents.agent]
id = "agent-2"

[agents.resource]
cpu = ["4", "5", "6", "7"]
mem = "32G"
devices = { cuda = ["cuda2", "cuda3"] }
```

### Applying Assignments

The `ResourceAllocator._apply_resource_assignments()` method takes assignments and creates agent-specific `ComputerContext` objects:

1. For `DevicePartition`: Filters `alloc_map.device_slots` to only include assigned device IDs
2. For `SlotPartition`: Scales slot amounts in `alloc_map.device_slots` to the configured values

### Validation

MANUAL mode validates configurations at startup:

- **Device name validation**: Configured device names must exist in discovered hardware
- **Device ID validation**: Configured device IDs must exist for the specified device
- **Exclusivity validation**: Same device ID cannot be assigned to multiple agents

Invalid configurations produce clear error messages that reference the new format.

## Migration / Compatibility

### Breaking Changes

**MANUAL mode config format changed:**

```toml
# Before (slot-based) - NO LONGER SUPPORTED
[agent.resource.allocations]
devices = { "cuda.mem" = 0.5, "cuda.shares" = 0.5 }

# After (device-based)
[agents.resource]
cpu = ["0", "1", "2", "3"]
mem = "16G"
devices = { cuda = ["cuda0", "cuda1"] }
```

### Backward Compatibility

- `SHARED` mode: No config change needed
- `AUTO_SPLIT` mode: No config change needed (devices auto-distributed)
- `MANUAL` mode: Config must be updated to use device IDs

Since no production systems use the multi-agent feature with non-SHARED modes, this breaking change has no practical impact.

### Error Messages for Old Format

Validators detect old slot-based config formats and provide helpful migration guidance:

```
Old slot-based format detected: key 'cuda.mem' contains '.'.
MANUAL mode now uses device-based format with device names as keys.
Example: cuda = ["cuda0", "cuda1"] instead of cuda.mem = 0.5.
```

## Implementation Plan

The implementation is split across multiple tickets/PRs for incremental review and to minimize risk.

### Ticket 1: Simplify to SHARED-only baseline (BA-4143, #8433)

**Goal**: Remove slot-based partitioning complexity by making all modes behave like SHARED temporarily.

**Changes**:
- Remove `_calculate_device_slot()` and related methods
- Make `AUTO_SPLIT` and `MANUAL` modes fall back to SHARED behavior
- All agents see all devices (no partitioning)

**Breaking**: Yes - temporary regression for AUTO_SPLIT and MANUAL modes.

### Ticket 2: Add device discovery infrastructure (BA-4144, #8440)

**Goal**: Introduce `GlobalDeviceInfo` and `GlobalDeviceMap` to separate device discovery from allocation.

**Changes**:
- Add `GlobalDeviceInfo` dataclass with plugin, devices, and alloc_map
- Add `_create_global_devices()` method
- Refactor `ResourceAllocator.__ainit__()` to use global device map

**Breaking**: No

### Ticket 3: Add ResourcePartitioner and AUTO_SPLIT (BA-4145, #8447)

**Goal**: Implement device-based partitioning for AUTO_SPLIT and SHARED modes.

**Changes**:
- Add `DevicePartition`, `SlotPartition`, and `Partition` types
- Add `ResourcePartitioner` class with assignment generation methods
- Add `_natural_sort_key()` for proper device ID ordering
- Implement `_apply_resource_assignments()` to apply partitions
- Implement scaling factor calculation

**Breaking**: No - restores AUTO_SPLIT functionality with device-based approach

### Ticket 4: Add device-based MANUAL mode (BA-4146, #8463)

**Goal**: Change MANUAL mode config from slot-based to device-based.

**Changes**:
- Change `ResourceAllocationConfig` to use separate `cpu`, `mem`, `devices` fields
- Implement `generate_manual_assignments()` in ResourcePartitioner
- Add validation for device names, device IDs, and exclusivity
- Add old format detection with helpful error messages

**Breaking**: Yes - MANUAL mode config format changes

## Implementation Notes

### Scaling Factors

When multiple agents share a host, each agent reports only a fraction of the host's total capacity to the manager. This prevents over-scheduling.

For AUTO_SPLIT mode, scaling factors are calculated proportionally based on actual device assignments. For example, if an agent receives 2 of 5 GPUs, its scaling factor for GPU slots is 0.4, not the simple 1/N that was used before.

### Memory Handling

Memory is a shared resource that doesn't have discrete device IDs like GPUs or CPU cores. In MANUAL mode, memory is specified as an amount (e.g., "16G") rather than device IDs. The implementation uses `SlotPartition` for memory assignments even in MANUAL mode.

### Unassigned Devices Warning

The implementation does not currently warn when devices exist on the system but are not assigned to any agent in MANUAL mode. This could be added as a future enhancement to help operators identify misconfigured systems.

## Open Questions

### Resolved

1. ~~**Migration tool for MANUAL mode configs**~~
   - **Decision: No** - No production systems use MANUAL mode, so a migration tool is unnecessary.

2. ~~**Plugins without discrete device IDs**~~
   - **Decision: Not applicable** - All compute plugins expose devices with discrete IDs. Memory is the exception, which is why it uses `SlotPartition` with amounts rather than device IDs.

## References

- [BEP-1002: Agent Architecture](BEP-1002-agent-architecture.md)
- [BEP-1016: Accelerator Interface v2](BEP-1016-accelerator-interface-v2.md)