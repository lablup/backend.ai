---
Author: Joongi Kim (joongi@lablup.com)
Status: Draft
Created: 2025-11-28
Created-Version:
Target-Version:
Implemented-Version:
---

# Accelerator Interface v2

## Related BEPs

- [BEP-1000](BEP-1000-redefining-accelerator-metadata.md) — Redefining Accelerator Metadata (variant properties, device metadata)
- [BEP-1047](BEP-1047-resource-slot-db-normalization.md) — Resource Slot DB Normalization

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

See [BEP-1000](BEP-1000-redefining-accelerator-metadata.md) for the new proposal and its comparison with the current design.

## Proposed Design

### Key Goals

* Make it applicable to non-Docker agent backends
    - Many existing plugin APIs are highly coupled with Docker-specific terminology and API parameter formats
* Allow programmatic extension of container lifecycle events
    - e.g., Interact with a vendor-provided device management service when creating or destroying new containers in a node
* Tidy up redundant and messy methods that only expose partial information
* Provide more detailed accelerator metadata ([BEP-1000](BEP-1000-redefining-accelerator-metadata.md))
* **NEW**: Replace module-level `PREFIX` constant and `key` class variable with `variant_namespace` abstract classmethod
* **NEW**: Report per-device variant properties (PEP-817-style 3-tuples) so the Manager/Scheduler can perform capability-aware placement
* **NEW**: Provide variant namespace descriptors that define match semantics, enabling provider-independent matching at the scheduler level

### Consolidating `PREFIX` and `key` into `variant_namespace`

#### Current State

Every accelerator plugin defines the same identifier in two redundant places:

```python
# Module-level constant (used by __all__ export, external references)
PREFIX = "cuda"

# Class-level attribute (used by agent plugin registry)
class CUDAPlugin(AbstractComputePlugin):
    key = DeviceName("cuda")
```

Affected plugins and their current PREFIX/key values:

| Plugin | `PREFIX` | `key` |
| ------ | -------- | ----- |
| `cuda_open` | `"cuda"` | `DeviceName("cuda")` |
| `rocm` | `"rocm"` | `DeviceName("rocm")` |
| `mock` | `"mock"` | `DeviceName(config["slot_name"])` (dynamic) |
| `ipu` | `"ipu"` | `DeviceName("ipu")` |
| `hyperaccel/lpu` | `"hyperaccel-lpu"` | `DeviceName(PREFIX)` |
| `furiosa/warboy` | `"warboy"` | `DeviceName("warboy")` |
| `furiosa/rngd` | `"rngd"` | `DeviceName("rngd")` |
| `habana/gaudi2` | `"gaudi2"` | `DeviceName("gaudi2")` |
| `habana/gaudi3` | `"gaudi3"` | `DeviceName("gaudi3")` |
| `rebellions/atom` | `"atom"` | `DeviceName("atom")` |
| `rebellions/atom_plus` | — | `DeviceName("atom-plus")` |
| `rebellions/atom_max` | — | `DeviceName("atom-max")` |
| `tenstorrent/n300` | `"tt-n300"` | `DeviceName("tt-n300")` |

Problems:
* The same string is declared twice — easy to drift out of sync.
* `PREFIX` is a plain module constant with no contract — plugins may or may not export it.
* Neither `PREFIX` nor `key` carries semantic meaning beyond "slot name prefix."
* The mock plugin dynamically sets `key` from config, proving that a class variable is not always sufficient.

#### Proposed Design

Replace both with a single **abstract classmethod** `variant_namespace` on `AbstractComputePlugin`.
The existing `key` property is derived from it for backward compatibility.

```python
# ai.backend.agent.resources
# --------------------------
from abc import ABCMeta, abstractmethod


class AbstractComputePlugin(AbstractPlugin, metaclass=ABCMeta):
    slot_types: Sequence[tuple[SlotName, SlotTypes]]
    exclusive_slot_types: set[str]

    @classmethod
    @abstractmethod
    def variant_namespace(cls) -> str:
        """Return the variant namespace that this plugin governs.

        This is the single source of truth for the plugin identity.
        It determines:
        - The namespace in PEP-817-style variant properties (e.g., "nvidia")
        - The DeviceName key used in the agent plugin registry (backward compat)
        - The resource slot prefix (e.g., "cuda" → "cuda.device", "cuda.shares")

        Must be a lowercase alphanumeric string with optional hyphens.
        """
        ...

    @property
    def key(self) -> DeviceName:
        """DeviceName key derived from variant_namespace (backward compatible)."""
        return DeviceName(self.variant_namespace())

    # ... rest of plugin interface ...
```

#### Migration Examples

**Before (CUDA plugin):**

```python
PREFIX = "cuda"

class CUDAPlugin(AbstractComputePlugin):
    key = DeviceName("cuda")
    slot_types = ((SlotName("cuda.device"), SlotTypes("count")),)

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "cuda.device",
            ...
        }
```

**After (CUDA plugin):**

```python
class CUDAPlugin(AbstractComputePlugin):
    slot_types = ((SlotName("cuda.device"), SlotTypes("count")),)

    @classmethod
    def variant_namespace(cls) -> str:
        return "nvidia"

    def get_variant_namespace_descriptors(self) -> Sequence[VariantNamespaceDescriptor]:
        return [VariantNamespaceDescriptor(
            namespace=self.variant_namespace(),
            features=[
                VariantFeatureDescriptor(
                    name="cuda_version",
                    match_mode=VariantMatchMode.MINIMUM,
                    ordered_values=["12.8", "12.6", "12.4", "12.2", "12.0", "11.8"],
                ),
                VariantFeatureDescriptor(
                    name="compute_capability",
                    match_mode=VariantMatchMode.MINIMUM,
                    ordered_values=["9.0", "8.9", "8.6", "8.0", "7.5", "7.0"],
                ),
                VariantFeatureDescriptor(
                    name="precision",
                    match_mode=VariantMatchMode.EXACT,
                    multi_value=True,
                    ordered_values=["fp64", "tf32", "bf16", "fp16", "fp8", "int8", "int4"],
                ),
            ],
        )]
```

**Before (mock plugin — dynamic key):**

```python
PREFIX = "mock"

class MockPlugin(AbstractComputePlugin):
    # key is set dynamically in init
    async def init(self, context: Any = None) -> None:
        self.key = DeviceName(self.mock_config["slot_name"])
```

**After (mock plugin — dynamic namespace via override):**

```python
class MockPlugin(AbstractComputePlugin):
    _namespace: str = "mock"

    @classmethod
    def variant_namespace(cls) -> str:
        return cls._namespace

    async def init(self, context: Any = None) -> None:
        # Override at instance level for testing flexibility
        self.__class__._namespace = self.mock_config.get("slot_name", "mock")
```

#### Backward Compatibility

The `key` property is preserved as a derived property from `variant_namespace()`.
Code that currently reads `plugin.key` will continue to work unchanged.

For external code that imports `PREFIX` from plugin modules, a module-level
backward-compat shim can be provided during the transition period:

```python
# ai.backend.accelerator.cuda_open.plugin (transition period)
# -----------------------------------------------------------
class CUDAPlugin(AbstractComputePlugin):
    @classmethod
    def variant_namespace(cls) -> str:
        return "nvidia"

# Backward compat: external code that does `from ... import PREFIX`
PREFIX = CUDAPlugin.variant_namespace()
```

Note that in the CUDA case, the variant namespace changes from `"cuda"` to `"nvidia"`
because PEP 817 namespaces identify the **vendor/provider** (e.g., `nvidia`), while the
Backend.AI `key`/resource slot prefix identifies the **technology** (e.g., `cuda`).
The `key` property can apply a namespace-to-device-name mapping if these differ:

```python
# Mapping for cases where vendor namespace differs from device name
_NAMESPACE_TO_DEVICE_NAME: dict[str, str] = {
    "nvidia": "cuda",
}

class AbstractComputePlugin(AbstractPlugin, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def variant_namespace(cls) -> str: ...

    @property
    def key(self) -> DeviceName:
        ns = self.variant_namespace()
        return DeviceName(_NAMESPACE_TO_DEVICE_NAME.get(ns, ns))
```

### `AbstractComputePlugin` API

| Function                                                          | Role                                                                                                                               |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `variant_namespace()` ✨ (abstract classmethod)                    | Return the variant namespace this plugin governs — single source of truth for plugin identity                                      |
| `key` ♻️ (derived property)                                       | `DeviceName` derived from `variant_namespace()` — backward compatible with existing plugin registry                                |
| `list_devices()`                                                  | List the available devices in the node                                                                                             |
| `configurable_slots()` ✨                                          | List the all possible resource slot types along with the display metadata                                                          |
| `available_slots()` ✨                                             | List the currently allocatable resource slot types as configured                                                                   |
| `create_alloc_map()`                                              | Create an `AbstractAllocMap` instance as configured                                                                                |
| `create_lifecycle_hook(workload, device_alloc)` ✨                 | Create an `AbstractLifecycleHook` instance                                                                                         |
| `alloc_to_devices(device_alloc)` ♻️                               | Extract the list of devices used in the given allocation, with their metadata                                                      |
| `gather_{node,workload,process}_metrics(stat_ctx[, target_id])` ♻ | Collects the raw metric values such as processor and memory utilization per node, workload (container or process tree), or process |
| `get_node_info()` ♻                                               | Get the node information such as driver/runtime versions and additional hardware info using a structured dataclass                 |
| `get_variant_namespace_descriptors()` ✨                           | Return namespace descriptors defining supported features and match semantics                                                       |

Here the "workload" means either a container or a (native) process tree, depending on the agent backend implementation.

### `AbstractComputeDevice` Struct

See [BEP-1000](BEP-1000-redefining-accelerator-metadata.md) for the new proposal.

Each device now carries a `variant_properties: Sequence[VariantProperty]` attribute
containing PEP-817-style 3-tuples that describe its capabilities. See BEP-1000 for
the data types and concrete examples.

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

## Agent → Manager Variant Property Reporting

### Heartbeat Extension

The Agent's periodic heartbeat to the Manager currently reports resource slot availability.
We extend it to also report per-device variant properties and namespace descriptors.

```python
# ai.backend.agent.server (heartbeat payload extension)
# -----------------------------------------------------
@attrs.define
class AgentHeartbeatPayload:
    # ... existing fields ...
    available_slots: Mapping[SlotName, Decimal]
    occupied_slots: Mapping[SlotName, Decimal]

    # NEW: per-device variant properties
    device_variant_properties: Mapping[
        DeviceName,                         # e.g., "cuda"
        Mapping[DeviceId, Sequence[str]]    # device_id → ["nvidia::cuda_version::12.8", ...]
    ]

    # NEW: namespace descriptors (match semantics)
    variant_namespace_descriptors: Mapping[
        str,  # namespace
        dict  # serialized VariantNamespaceDescriptor
    ]
```

### Agent-Side Collection

```python
# ai.backend.agent.resources
# --------------------------
class AbstractComputePlugin(AbstractPlugin, metaclass=ABCMeta):
    # ... existing methods ...

    @abstractmethod
    def get_variant_namespace_descriptors(self) -> Sequence[VariantNamespaceDescriptor]:
        """Return namespace descriptors defining the variant features this plugin supports.

        Each descriptor specifies:
        - The namespace this plugin governs
        - Available features with their match modes (EXACT, MINIMUM, COMPATIBLE)
        - Whether each feature accepts multiple values
        - Ordered values from most-preferred to least-preferred

        The returned descriptors are reported to the Manager and used by the
        Sokovan scheduler for provider-independent matching logic.
        """
        return []
```

The Agent collects variant properties from each plugin:

```python
# ai.backend.agent.server (heartbeat collection logic)
# -----------------------------------------------------
async def _collect_device_variant_properties(
    self,
    compute_plugins: Mapping[DeviceName, AbstractComputePlugin],
) -> tuple[
    dict[DeviceName, dict[DeviceId, list[str]]],
    dict[str, dict],
]:
    device_variants: dict[DeviceName, dict[DeviceId, list[str]]] = {}
    namespace_descriptors: dict[str, dict] = {}

    for device_name, plugin in compute_plugins.items():
        devices = await plugin.list_devices()
        per_device: dict[DeviceId, list[str]] = {}
        for device in devices:
            per_device[device.device_id] = [
                str(vp) for vp in device.variant_properties
            ]
        device_variants[device_name] = per_device

        for ns_desc in plugin.get_variant_namespace_descriptors():
            namespace_descriptors[ns_desc.namespace] = attrs.asdict(ns_desc)

    return device_variants, namespace_descriptors
```

### Manager-Side Storage

On receiving a heartbeat, the Manager upserts the reported variant data into the DB tables
defined in BEP-1000 (`agent_device_variant_properties`, `agent_variant_namespace_descriptors`).

```python
# ai.backend.manager.services.agent
# ----------------------------------
async def _update_device_variant_properties(
    self,
    db_session: AsyncSession,
    agent_id: AgentId,
    device_variants: Mapping[str, Mapping[str, Sequence[str]]],
    namespace_descriptors: Mapping[str, dict],
) -> None:
    """Upsert device variant properties from agent heartbeat.

    Strategy: DELETE existing + INSERT new (simpler than per-row upsert
    given that the full state is reported each heartbeat).
    """
    # Clear existing variant properties for this agent
    await db_session.execute(
        sa.delete(AgentDeviceVariantPropertyRow)
        .where(AgentDeviceVariantPropertyRow.agent_id == agent_id)
    )

    # Insert new properties
    rows = []
    for device_name, devices in device_variants.items():
        for device_id, props in devices.items():
            for prop_str in props:
                vp = VariantProperty.from_str(prop_str)
                rows.append(AgentDeviceVariantPropertyRow(
                    agent_id=agent_id,
                    device_name=device_name,
                    device_id=device_id,
                    namespace=vp.namespace,
                    feature_name=vp.feature_name,
                    feature_value=vp.feature_value,
                ))
    if rows:
        db_session.add_all(rows)

    # Upsert namespace descriptors
    await db_session.execute(
        sa.delete(AgentVariantNamespaceDescriptorRow)
        .where(AgentVariantNamespaceDescriptorRow.agent_id == agent_id)
    )
    for namespace, descriptor in namespace_descriptors.items():
        db_session.add(AgentVariantNamespaceDescriptorRow(
            agent_id=agent_id,
            namespace=namespace,
            descriptor=descriptor,
        ))
```

## Sokovan Scheduler: Variant-Aware Agent Selection

### Overview

<!--context-for-ai
The current Sokovan scheduler's AgentSelector performs a 3-pass selection:
1. Architecture filter (binary compatibility)
2. Resource availability filter (quantitative slot comparison)
3. Failed-agent deprioritization
We add a new pass between #1 and #2 for variant property matching (qualitative).
-->

The current Sokovan scheduler (`AgentSelector`) selects agents in three passes:

1. **Architecture filter** — binary compatibility check (e.g., x86_64 vs aarch64)
2. **Resource availability** — quantitative slot check (available >= requested)
3. **Failed-agent deprioritization** — avoid agents that previously failed for this session

We add a new **variant compatibility pass** between #1 and #2 that filters agents based on
whether they have devices whose variant properties satisfy the workload's requirements.

### Workload Variant Requirements

A session creation request can now include variant requirements:

```python
# ai.backend.common.types
# -----------------------
@attrs.define(frozen=True)
class VariantRequirement:
    """A single requirement on device variant properties.

    For MINIMUM match mode: "I need a device with cuda_version >= 12.6"
    For EXACT match mode: "I need a device with precision == bf16"
    """
    namespace: str
    feature_name: str
    feature_value: str

    def __str__(self) -> str:
        return f"{self.namespace}::{self.feature_name}::{self.feature_value}"

    @classmethod
    def from_str(cls, s: str) -> VariantRequirement:
        parts = s.split("::")
        if len(parts) != 3:
            raise ValueError(f"Invalid variant requirement: {s!r}")
        return cls(namespace=parts[0], feature_name=parts[1], feature_value=parts[2])
```

```python
# Extended ResourceRequirements in the scheduler
@dataclass
class ResourceRequirements:
    requested_slots: ResourceSlot
    required_architecture: str
    kernel_ids: Sequence[UUID]
    variant_requirements: Sequence[VariantRequirement] = field(default_factory=list)  # NEW
```

### Extended Agent Selection Flow

```python
# ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector
# -------------------------------------------------------------------
class AgentSelector:

    async def _select_agent_tracker_for_requirements(
        self,
        state_trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        designated_agent_ids: list[AgentId] | None = None,
    ) -> AgentStateTracker:
        # Pass 1: Architecture compatibility (unchanged)
        arch_compatible_trackers = self._filter_by_architecture(
            state_trackers, resource_req.required_architecture,
        )

        # Pass 1.5 (NEW): Variant property compatibility
        if resource_req.variant_requirements:
            variant_compatible_trackers = await self._filter_by_variant_properties(
                arch_compatible_trackers,
                resource_req.variant_requirements,
                resource_req.requested_slots,
            )
        else:
            variant_compatible_trackers = arch_compatible_trackers

        # Pass 2: Resource availability (unchanged, but now on variant-filtered set)
        compatible_trackers = self._filter_by_resource_availability(
            variant_compatible_trackers, resource_req, config,
        )

        # Pass 3: Failed-agent deprioritization (unchanged)
        candidate_trackers = self._deprioritize_failed_agents(
            compatible_trackers, criteria,
        )

        return self._strategy.select_tracker_by_strategy(
            candidate_trackers, resource_req, criteria, config,
        )
```

### Variant Filtering Implementation

```python
# ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector
# -------------------------------------------------------------------
class AgentSelector:

    async def _filter_by_variant_properties(
        self,
        trackers: Sequence[AgentStateTracker],
        variant_reqs: Sequence[VariantRequirement],
        requested_slots: ResourceSlot,
    ) -> list[AgentStateTracker]:
        """Filter agents that have at least one device satisfying all variant requirements.

        The check is: for the resource slot types being requested (e.g., cuda.device),
        does the agent have physical devices whose variant properties satisfy ALL
        of the variant requirements?
        """
        # Determine which device_name(s) are relevant from requested slots
        # e.g., "cuda.device" or "cuda.shares" → device_name "cuda"
        relevant_device_names = {
            slot_name.split(".")[0]
            for slot_name in requested_slots.keys()
            if "." in slot_name
        }
        if not relevant_device_names:
            return list(trackers)

        # Batch-load variant data for all candidate agents
        agent_ids = [t.original_agent.agent_id for t in trackers]
        device_props_by_agent = await self._variant_repo.get_device_variant_properties(
            agent_ids, relevant_device_names,
        )
        ns_descriptors = await self._variant_repo.get_namespace_descriptors(agent_ids)

        compatible: list[AgentStateTracker] = []
        variant_errors: dict[AgentId, str] = {}

        for tracker in trackers:
            agent_id = tracker.original_agent.agent_id
            agent_device_props = device_props_by_agent.get(agent_id, {})
            agent_ns_descs = ns_descriptors.get(agent_id, {})

            # Check if ANY device on this agent satisfies ALL requirements
            has_compatible_device = False
            for device_name in relevant_device_names:
                devices = agent_device_props.get(device_name, {})
                for device_id, props in devices.items():
                    if check_variant_compatibility(
                        required=[
                            VariantProperty(r.namespace, r.feature_name, r.feature_value)
                            for r in variant_reqs
                        ],
                        device_props=props,
                        namespace_descriptors=agent_ns_descs,
                    ):
                        has_compatible_device = True
                        break
                if has_compatible_device:
                    break

            if has_compatible_device:
                compatible.append(tracker)
            else:
                variant_errors[agent_id] = _format_variant_mismatch(
                    variant_reqs, agent_device_props, agent_ns_descs,
                )

        if not compatible:
            raise NoCompatibleAgentError(
                _build_variant_error_message(variant_reqs, variant_errors)
            )

        return compatible
```

### Error Messages for Variant Mismatches

When resource slots are quantitatively available but no device matches the variant requirements,
the user needs a clear explanation:

```python
# ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions
# ---------------------------------------------------------------------
class VariantPropertyMismatchError(NoCompatibleAgentError):
    """Raised when agents have sufficient resource slots but no devices match variant requirements."""

    def __init__(
        self,
        variant_requirements: Sequence[VariantRequirement],
        available_agents: int,
        details: str,
    ) -> None:
        req_strs = [str(r) for r in variant_requirements]
        super().__init__(
            f"No agents have devices matching the required accelerator capabilities. "
            f"{available_agents} agent(s) have sufficient resource slots, but none have "
            f"devices satisfying: [{', '.join(req_strs)}]. {details}"
        )
        self.variant_requirements = variant_requirements
        self.available_agents = available_agents


def _format_variant_mismatch(
    reqs: Sequence[VariantRequirement],
    agent_device_props: Mapping[str, Mapping[str, Sequence[VariantProperty]]],
    ns_descriptors: Mapping[str, VariantNamespaceDescriptor],
) -> str:
    """Build a human-readable mismatch explanation for a single agent."""
    lines = []
    for req in reqs:
        ns_desc = ns_descriptors.get(req.namespace)
        feat_desc = None
        if ns_desc:
            for fd in ns_desc.features:
                if fd.name == req.feature_name:
                    feat_desc = fd
                    break

        match_mode = feat_desc.match_mode if feat_desc else VariantMatchMode.EXACT
        if match_mode == VariantMatchMode.MINIMUM:
            lines.append(
                f"  requires {req.namespace}::{req.feature_name} >= {req.feature_value}"
            )
        else:
            lines.append(
                f"  requires {req.namespace}::{req.feature_name} == {req.feature_value}"
            )

    # Show what the agent actually has
    for device_name, devices in agent_device_props.items():
        for device_id, props in devices.items():
            prop_strs = [str(p) for p in props]
            lines.append(f"  device {device_name}/{device_id} has: {prop_strs}")

    return "\n".join(lines)


def _build_variant_error_message(
    reqs: Sequence[VariantRequirement],
    agent_errors: Mapping[AgentId, str],
) -> str:
    """Build a summary error message across all agents."""
    summary_parts = []
    # Group agents by similar mismatch reasons
    reason_counts: dict[str, int] = defaultdict(int)
    for agent_id, reason in agent_errors.items():
        first_line = reason.split("\n")[0]
        reason_counts[first_line] += 1

    for reason, count in reason_counts.items():
        summary_parts.append(f"{count}x agent(s): {reason}")

    return (
        f"Variant requirements not satisfiable: [{', '.join(str(r) for r in reqs)}]. "
        + "; ".join(summary_parts)
    )
```

### Example: Error Message Scenarios

**Scenario 1**: User requests `cuda.device=2` with variant `nvidia::compute_capability::9.0` (Blackwell),
but only Ampere (8.0) GPUs are available.

```
SessionSchedulingError: No agents have devices matching the required accelerator capabilities.
3 agent(s) have sufficient resource slots, but none have devices satisfying:
[nvidia::compute_capability::9.0].
  3x agent(s): requires nvidia::compute_capability >= 9.0
  Closest available: nvidia::compute_capability == 8.0 (NVIDIA A100)
```

**Scenario 2**: User requests `cuda.device=1` with variant `nvidia::precision::fp8`,
but only Volta (V100, no FP8) GPUs are available.

```
SessionSchedulingError: No agents have devices matching the required accelerator capabilities.
2 agent(s) have sufficient resource slots, but none have devices satisfying:
[nvidia::precision::fp8].
  2x agent(s): requires nvidia::precision == fp8
  Available precisions: fp64, fp32, fp16
```

## Resource Group Variant-Aware Availability API

### Motivation

When users query available resources in a resource group, the current API returns
aggregate slot quantities. With variant properties, users need to know not just
"how many GPUs are free" but "how many GPUs with compute capability >= 8.0 are free."

### API Design

```
POST /resource-group/{rg_id}/available-slots
```

**Request body (optional variant filter):**

```json
{
  "variant_filter": [
    {"namespace": "nvidia", "feature_name": "compute_capability", "feature_value": "8.0"},
    {"namespace": "nvidia", "feature_name": "precision", "feature_value": "bf16"}
  ]
}
```

**Response:**

```json
{
  "available_slots": {
    "cpu": "32.0",
    "mem": "137438953472",
    "cuda.device": "4.0",
    "cuda.shares": "4.0"
  },
  "variant_matched_devices": {
    "cuda": {
      "total_devices": 8,
      "matched_devices": 4,
      "unmatched_reasons": {
        "nvidia::compute_capability::8.0": {
          "unsatisfied_count": 4,
          "closest_values": ["7.5"]
        }
      }
    }
  }
}
```

### Implementation

```python
# ai.backend.manager.services.resource_group
# -------------------------------------------
async def get_available_slots_with_variant_filter(
    self,
    resource_group_id: UUID,
    variant_filter: Sequence[VariantRequirement] | None = None,
) -> VariantAwareAvailability:
    """Query available resource slots, optionally filtered by variant properties.

    When variant_filter is provided, only devices whose variant properties
    satisfy ALL filter conditions are counted toward the available slots
    for accelerator resource types.
    """
    async with self.db.begin_readonly_session() as db_session:
        # Step 1: Get all agents in the resource group
        agents = await self._agent_repo.list_by_resource_group(
            db_session, resource_group_id,
        )

        if not variant_filter:
            # No filter: return standard aggregate availability
            return await self._compute_aggregate_availability(db_session, agents)

        # Step 2: For each agent, find devices matching the variant filter
        agent_ids = [a.id for a in agents]
        device_props = await self._variant_repo.get_device_variant_properties(
            db_session, agent_ids,
        )
        ns_descriptors = await self._variant_repo.get_namespace_descriptors(
            db_session, agent_ids,
        )

        # Step 3: Compute variant-aware availability
        return await self._compute_variant_filtered_availability(
            db_session, agents, device_props, ns_descriptors, variant_filter,
        )


async def _compute_variant_filtered_availability(
    self,
    db_session: AsyncSession,
    agents: Sequence[AgentMeta],
    device_props: Mapping[AgentId, Mapping[str, Mapping[str, Sequence[VariantProperty]]]],
    ns_descriptors: Mapping[AgentId, Mapping[str, VariantNamespaceDescriptor]],
    variant_filter: Sequence[VariantRequirement],
) -> VariantAwareAvailability:
    """Compute available slots considering variant property constraints.

    For accelerator slots: only count capacity from devices that match the filter.
    For non-accelerator slots (cpu, mem): return unchanged aggregates.
    """
    total_slots = ResourceSlot()
    occupied_slots = ResourceSlot()
    match_summary: dict[str, DeviceMatchSummary] = {}

    for agent in agents:
        agent_id = agent.id
        agent_device_props = device_props.get(agent_id, {})
        agent_ns_descs = ns_descriptors.get(agent_id, {})

        for device_name, devices in agent_device_props.items():
            total_count = len(devices)
            matched_count = 0
            for device_id, props in devices.items():
                if check_variant_compatibility(
                    required=[
                        VariantProperty(r.namespace, r.feature_name, r.feature_value)
                        for r in variant_filter
                    ],
                    device_props=props,
                    namespace_descriptors=agent_ns_descs,
                ):
                    matched_count += 1

            if device_name not in match_summary:
                match_summary[device_name] = DeviceMatchSummary(
                    total_devices=0, matched_devices=0,
                )
            match_summary[device_name].total_devices += total_count
            match_summary[device_name].matched_devices += matched_count

    # ... aggregate slot quantities from matched devices only ...

    return VariantAwareAvailability(
        available_slots=total_slots - occupied_slots,
        variant_matched_devices=match_summary,
    )
```

### GraphQL Query Extension

```python
# ai.backend.manager.api.gql.resource_group (Strawberry schema)
# --------------------------------------------------------------
@strawberry.input
class VariantFilterInput:
    namespace: str
    feature_name: str
    feature_value: str


@strawberry.type
class VariantMatchedDevices:
    total_devices: int
    matched_devices: int


@strawberry.type
class VariantAwareAvailabilityNode:
    available_slots: JSONString
    variant_matched_devices: list[VariantMatchedDevices]


@strawberry.type
class ResourceGroupQuery:
    @strawberry.field
    async def available_slots(
        self,
        info: Info,
        resource_group_id: UUID,
        variant_filter: list[VariantFilterInput] | None = None,
    ) -> VariantAwareAvailabilityNode:
        ...
```

## Session Creation with Variant Requirements

### REST API

```
POST /v2/sessions/
```

```json
{
  "image": "cr.backend.ai/stable/pytorch:2.5-cuda12.8-py3.12",
  "resources": {
    "cpu": 4,
    "mem": "16g",
    "cuda.device": 2
  },
  "variant_requirements": [
    "nvidia::compute_capability::8.0",
    "nvidia::precision::bf16"
  ]
}
```

### GraphQL Mutation

```graphql
mutation {
  createSession(
    image: "cr.backend.ai/stable/pytorch:2.5-cuda12.8-py3.12"
    resources: {cpu: 4, mem: "16g", "cuda.device": 2}
    variantRequirements: [
      "nvidia::compute_capability::8.0"
      "nvidia::precision::bf16"
    ]
  ) {
    sessionId
    status
  }
}
```

## Variant Property Discovery API

Users need to discover what variant properties are available in their accessible resource groups.

```
GET /v2/resource-groups/{rg_id}/variant-properties
```

**Response:**

```json
{
  "namespaces": {
    "nvidia": {
      "features": [
        {
          "name": "cuda_version",
          "match_mode": "minimum",
          "multi_value": false,
          "available_values": ["12.8", "12.6", "12.4"]
        },
        {
          "name": "compute_capability",
          "match_mode": "minimum",
          "multi_value": false,
          "available_values": ["9.0", "8.0", "7.5"]
        },
        {
          "name": "precision",
          "match_mode": "exact",
          "multi_value": true,
          "available_values": ["fp64", "tf32", "bf16", "fp16", "fp8", "int8"]
        },
        {
          "name": "gpu_arch",
          "match_mode": "exact",
          "multi_value": false,
          "available_values": ["hopper", "ampere", "turing"]
        }
      ]
    }
  }
}
```

This endpoint aggregates variant namespace descriptors and actual device properties
across all agents in the resource group, so the client can present meaningful
filter options to the user.

## Discussion

* How to handle & distinguish in-place restarts and relocated restarts in lifecycle hooks?
* Would it better to provide a managed state-store interface to the lifecycle hook instances instead of requiring them to be stateless?
* A better naming for "workload"?
    - Just keep using "kernel" in align with the cluster-wide scheduler?
    - Need to consider the relationship with "session" as well...
* **NEW**: Should variant requirements be expressible in session templates / resource presets?
    - e.g., A "deep learning" preset could include `nvidia::precision::bf16` by default.
* **NEW**: How to handle variant property changes when an agent's driver is upgraded mid-operation?
    - Proposed: re-report on next heartbeat; running sessions are unaffected; new sessions see updated properties.
* **NEW**: Should we support negative variant requirements? (e.g., "NOT nvidia::partitioning::mig")
    - PEP 817 does not support negation; keeping it simple seems better initially.
* **NEW**: Caching strategy for variant data in the scheduler?
    - Since heartbeats are periodic, the scheduler snapshot can include a materialized view of variant properties alongside resource slot data.
