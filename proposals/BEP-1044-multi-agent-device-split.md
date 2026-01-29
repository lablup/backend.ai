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

## Motivation

As part of the Accelerator Interface v2 redesign ([BEP-1016](BEP-1016-accelerator-interface-v2.md)), we are moving toward device-centric resource management. The current slot-based allocation model is an abstraction mismatch that complicates multi-agent resource partitioning.

The previous multi-agent resource allocation used **slot-based** configuration where devices were specified by slot names with decimal fractional values:

```toml
[agent.resource.allocations]
devices = { "cuda.mem" = 0.3, "cuda.shares" = 0.5 }
```

This approach has problems:

1. **No device exclusivity**: Slot-based allocation divides abstract quantities (e.g., "0.5 of cuda.shares") but cannot enforce that agents use mutually exclusive physical devices. For CPU cores and accelerators, multiple agents must not share the same device - slot amounts alone cannot express or enforce this.

2. **Abstraction mismatch**: The actual resource being partitioned is a set of physical devices (cuda0, cuda1, etc.), not slot amounts. Slot names like `cuda.mem` and `cuda.shares` are derived properties - we should configure at the device level and derive slots from that, not the other way around.

## Current Design

### Configuration (Before)

```python
class ResourceAllocationConfig(BaseConfigSchema):
    devices: Mapping[SlotNameField, Decimal]
    # Example: {"cuda.mem": Decimal("0.5"), "cuda.shares": Decimal("0.5")}
```

### Slot Calculation (Before)

The `ResourceAllocator` uses `_calculate_device_slot_*` methods to compute slot amounts:

```python
def _calculate_device_slot(self, slot_name, agent_idx, agent_config, alloc_map_type):
    match agent_config.resource.allocation_mode:
        case ResourceAllocationMode.SHARED:
            return self._calculate_device_slot_shared(slot_name)
        case ResourceAllocationMode.AUTO_SPLIT:
            return self._calculate_device_slot_auto_split(slot_name, alloc_map_type, agent_idx)
        case ResourceAllocationMode.MANUAL:
            return self._calculate_device_slot_manual(slot_name, agent_config)
```

This tightly couples slot calculation with allocation modes and operates on abstract slot amounts rather than concrete devices.

## Proposed Design

### Configuration (After)

```python
class ResourceAllocationConfig(BaseConfigSchema):
    devices: Mapping[DeviceName, Sequence[DeviceId]]
    # Example: {"cuda": [DeviceId("cuda0"), DeviceId("cuda1")]}
```

### Device-Based Allocation

Instead of calculating slot amounts, the new design:

1. **Discovers actual devices** from plugins (e.g., `cuda0`, `cuda1`, `cuda2`)
2. **Assigns specific device IDs** to each agent
3. **Slot amounts derived** from assigned devices (not the other way around)

### Device Partitioner Abstraction

```python
class DevicePartitioner(Protocol):
    """Protocol for generating device assignments in AUTO_SPLIT mode."""
    device_name: DeviceName

    def generate_assignments(
        self,
        devices: Sequence[AbstractComputeDevice],
        agent_ids: Sequence[AgentId],
    ) -> Mapping[AgentId, Sequence[DeviceId]]: ...
```

Two implementations:

1. **WholeDevicePartitioner**: For CPU and accelerators - assigns whole devices using fill-from-front
2. **SharedDevicePartitioner**: For memory - all agents share the same device ID (amount is split separately)

### Fill-From-Front Distribution

```python
def distribute_devices(device_ids, agent_ids) -> dict[AgentId, list[DeviceId]]:
    """
    For N devices across M agents:
    - q, r = divmod(N, M)
    - First r agents get (q + 1) devices
    - Remaining agents get q devices
    - Devices assigned in natural sorted order
    """
```

Example: 5 GPUs across 3 agents → [2, 2, 1] distribution

### Natural Sort for Device IDs

Device IDs are sorted using natural sort to handle numeric suffixes correctly:

```python
def _natural_sort_key(device_id: DeviceId) -> list[str | int]:
    # "cuda0", "cuda1", "cuda10" sorts correctly (not lexicographically)
    # Handles: "0", "10" and "nvme0n1p1", "nvme0n1p10"
```

### Unified Assignment Flow

Both `AUTO_SPLIT` and `MANUAL` modes produce the same `DeviceAssignments` structure:

```python
type DeviceAssignments = Mapping[AgentId, Mapping[DeviceName, Sequence[DeviceId]]]
```

This is then applied via `_apply_device_assignments()` which:
1. Filters each agent's devices to only assigned ones
2. Updates `alloc_map.device_slots` accordingly
3. For memory, recalculates slot amounts based on mode

## Migration / Compatibility

### Breaking Changes

**Config format changed for MANUAL mode:**

```toml
# Before (slot-based)
[agent.resource.allocations]
devices = { "cuda.mem" = 0.5, "cuda.shares" = 0.5 }

# After (device-based)
[agent.resource.allocations.devices]
cuda = ["cuda0", "cuda1"]
```

### Backward Compatibility

- `SHARED` mode: No config change needed
- `AUTO_SPLIT` mode: No config change needed (devices auto-distributed)
- `MANUAL` mode: Config must be updated to use device IDs

## Implementation Plan

The implementation is split across multiple tickets/PRs for incremental review and to minimize risk. Each ticket (except the first) includes tests for the functionality it adds.

### Ticket 1: Simplify to SHARED-only baseline

**Goal**: Remove slot-based partitioning complexity by making all modes behave like SHARED temporarily.

**Changes**:
- Remove `_calculate_device_slot()` and related methods
- Remove `_calculate_device_slot_shared()`, `_calculate_device_slot_auto_split()`, `_calculate_device_slot_manual()`
- Make `AUTO_SPLIT` and `MANUAL` modes fall back to SHARED behavior
- All agents see all devices (no partitioning)
- Remove or skip tests for partitioning behavior (they will fail until restored)

**Breaking**: Yes - `AUTO_SPLIT` and `MANUAL` modes will not partition resources. This is intentional to establish a clean baseline.

### Ticket 2: Add device discovery and global device map

**Goal**: Introduce `GlobalDeviceInfo` and `GlobalDeviceMap` to separate device discovery from allocation.

**Changes**:
- Add `GlobalDeviceInfo` dataclass (plugin + devices, no alloc_map)
- Add `_create_global_devices()` method
- Refactor `ResourceAllocator.__ainit__()` to use global device map
- Change `_calculate_total_slots()` to use `plugin.available_slots()` directly

**Tests**:
- Unit tests for `GlobalDeviceInfo` structure
- Tests for `_create_global_devices()` with mock plugins

**Breaking**: No

### Ticket 3: Add DevicePartitioner and AUTO_SPLIT device distribution

**Goal**: Implement device-based partitioning for AUTO_SPLIT mode.

**Changes**:
- Add `DevicePartitioner` protocol
- Add `WholeDevicePartitioner` (for CPU, accelerators)
- Add `SharedDevicePartitioner` (for memory)
- Add `distribute_devices()` with fill-from-front algorithm
- Add `_natural_sort_key()` for proper device ID ordering
- Implement `_generate_auto_split_assignments()`
- Implement `_apply_device_assignments()`

**Tests**:
- Unit tests for `distribute_devices()` (various N devices / M agents combinations)
- Unit tests for `_natural_sort_key()` (numeric, prefixed, complex IDs)
- Unit tests for `WholeDevicePartitioner` and `SharedDevicePartitioner`
- Integration tests for AUTO_SPLIT mode multi-agent scenarios

**Breaking**: No - restores AUTO_SPLIT functionality with device-based approach

### Ticket 4: Add device-based MANUAL mode configuration

**Goal**: Change MANUAL mode config from slot-based to device-based.

**Changes**:
- Change `ResourceAllocationConfig.devices` type from `Mapping[SlotName, Decimal]` to `Mapping[DeviceName, Sequence[DeviceId]]`
- Implement `_read_manual_assignments()`
- Add validation: `_validate_device_names_exist()`, `_validate_device_ids_exist()`, `_validate_device_mutual_exclusivity()`, `_warn_unassigned_devices()`
- Update config examples and documentation

**Tests**:
- Unit tests for config parsing with new device-based format
- Unit tests for validation functions (invalid device names, duplicate assignments, etc.)
- Integration tests for MANUAL mode multi-agent scenarios

**Breaking**: Yes - MANUAL mode config format changes

## Open Questions

### Resolved

1. ~~**Migration tool for MANUAL mode configs**~~
   - **Decision: No** - MANUAL mode config format change is a breaking change, but users can update configs manually. A migration tool would be over-engineering given the small number of MANUAL mode users.

2. ~~**Plugins without discrete device IDs**~~
   - **Decision: Not applicable** - All compute plugins expose devices via `/dev/` or `/sys/` paths which inherently have discrete IDs (e.g., `cuda0`, `cpu0`). Memory is the exception, which is why `SharedDevicePartitioner` exists - it doesn't require device exclusivity and shares the same device ID across all agents.

## References

- [BEP-1002: Agent Architecture](BEP-1002-agent-architecture.md)
- [BEP-1016: Accelerator Interface v2](BEP-1016-accelerator-interface-v2.md)