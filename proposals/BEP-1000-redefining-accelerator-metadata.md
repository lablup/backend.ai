---
Author: Joongi Kim (joongi@lablup.com)
Status: Draft
Created:
Created-Version:
Target-Version:
Implemented-Version:
---

# Redefining Accelerator Metadata

## Related BEPs

- [BEP-1016](BEP-1016-accelerator-interface-v2.md) — Accelerator Interface v2 (plugin API redesign)
- [BEP-1047](BEP-1047-resource-slot-db-normalization.md) — Resource Slot DB Normalization

## Current structure

```python
# ai.backend.common.types
# -----------------------
class ResourceSlotReprFormat(TypedDict):
    # I'd propose to rename this from AcceleratorNumberFormat.
    binary: bool
    round_length: int


class AcceleratorMetadata(TypedDict):
    slot_name: str
    description: str
    human_readable_name: str
    display_unit: str
    display_icon: str
    number_format: ResourceSlotReprFormat


# ai.backend.agent.resources
# --------------------------
class AbstractComputeDevice:
    device_id: DeviceId
    hw_location: str  # either PCI bus ID or arbitrary string
    memory_size: int  # bytes of available per-accelerator memory
    processing_units: int  # number of processing units (e.g., cores, SMP)
    numa_node: Optional[int]  # NUMA node ID (None if not applicable)

    ...

class AbstractComputePlugin(AbstractPlugin, metaclass=ABCMeta):
    key: DeviceName = DeviceName("accelerator")
    slot_types: Sequence[tuple[SlotName, SlotTypes]]
    exclusive_slot_types: set[str]

    @abstractmethod
    def get_metadata(self) -> AcceleratorMetadata: ...

    @abstractmethod
    async def list_devices(self) -> Collection[AbstractComputeDevice]: ...

    @abstractmethod
    async def available_slots(self) -> Mapping[SlotName, Decimal]: ...

    @abstractmethod
    def get_version(self) -> str: ...

    @abstractmethod
    async def extra_info(self) -> Mapping[str, str]: ...

    @abstractmethod
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]: ...

    @abstractmethod
    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]: ...

    @abstractmethod
    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]: ...

    @abstractmethod
    async def create_alloc_map(self) -> AbstractAllocMap: ...

    @abstractmethod
    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]: ...

    @abstractmethod
    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: DeviceAllocation,
    ) -> Mapping[str, Any]: ...

    async def generate_resource_data(self, device_alloc: DeviceAllocation) -> Mapping[str, str]: ...

    @abstractmethod
    async def restore_from_container(
        self,
        container: SessionContainer,
        alloc_map: AbstractAllocMap,
    ) -> None: ...

    @abstractmethod
    async def get_attached_devices(
        self,
        device_alloc: DeviceAllocation,
    ) -> Sequence[DeviceModelInfo]: ...

    async def get_node_hwinfo(self) -> HardwareMetadata: ...

    @abstractmethod
    async def get_docker_networks(
        self,
        device_alloc: DeviceAllocation,
    ) -> list[str]: ...

    @abstractmethod
    async def generate_mounts(
        self,
        source_path: Path,
        device_alloc: DeviceAllocation,
    ) -> list[MountInfo]: ...

    def get_additional_gids(self) -> list[int]: ...

    def get_additional_allowed_syscalls(self) -> list[str]: ...
```

### Problems

* A single plugin may return only one `AcceleratorMetadata`.
  - e.g., If the cuda plugin has multiple devices with different configurations (e.g., 2 GPUs with MIG enabled and 6 GPUs without it), it cannot return two different AcceleratorMetadata instances.
* It is confusing whether `AcceleratorMetadata` represents a resource slot or a device (it's for resource slot!). The name should be clarified.
* We need to expand the metadata format to include various device capabilities such as compute precision support, partition capability, and memory hierarchy.
* The metadata is only used at Agent level and is not structured for consumption by the Manager/Scheduler. The Sokovan scheduler cannot make device-capability-aware placement decisions.
* Every plugin redundantly defines the same identifier twice — a module-level `PREFIX` constant and a class-level `key` attribute — with no enforced contract between them (see BEP-1016 for the consolidation proposal using `variant_namespace`).

## Proposed structure

### Hardware Specification Types

```python
# ai.backend.common.types
# -----------------------
class ComputePrecisionSupportLevel(enum.StrEnum):
    NATIVE = enum.auto()
    EMULATED = enum.auto()
    NONE = enum.auto()


@attrs.define(auto_attribs=True)
class ComputePrecisionSupport:
    format: str  # e.g., "FP32", "TF32", "BF16", "FP16", "FP8", "INT8", "INT4", "FP4"
    support: ComputePrecisionSupportLevel


@attrs.define(auto_attribs=True)
class ComputeUnit:
    name: str  # e.g., "SM", "Tensor Core", "GPC", "CU", "TPC", "AI Core"
    count: int  # Number of such units in the device


@attrs.define(auto_attribs=True)
class MemorySpec:
    total_memory: int  # Total on-device memory capacity in bytes
    memory_type: str   # e.g., "HBM2", "HBM3", "GDDR6", "DDR5"
    bandwidth: Optional[float] = None          # Peak memory bandwidth in GiB/s
    l1_cache_per_core: Optional[int] = None    # L1 cache size per compute unit (bytes)
    l2_cache: Optional[int] = None             # L2 cache size (bytes, chip-wide or per die)
    shared_mem_per_core: Optional[int] = None  # Size of programmable shared memory per core (bytes)
    memory_channels: Optional[int] = None      # Number of memory channels or HBM stacks


@attrs.define(auto_attribs=True)
class PartitioningCapability:
    max_partitions: int = 1           # Maximum number of slices/partitions
    technology: Optional[str] = None  # Name of partitioning method (e.g., "MIG", "fGPU")
```

### Variant Properties (inspired by PEP 817)

<!--context-for-ai
PEP 817 defines wheel variant properties as 3-tuples of (namespace, feature_name, feature_value).
We adopt this same format so that the matching logic in the scheduler is generic and provider-independent.
Each accelerator plugin acts as a "variant provider" that reports its supported properties per device.
The scheduler acts as the "install-time matcher" that checks workload requirements against device properties.
-->

[PEP 817 (Wheel Variant Support)](https://wheelnext.dev/proposals/pep817_wheel_variant_support/)
defines a **variant property** as a 3-tuple `(namespace, feature_name, feature_value)` that describes
a specific capability of a build target. Key design principles from PEP 817:

1. **Provider-independent matching**: The matching algorithm only checks set membership and ordering —
   it does not need to understand the semantics of individual providers.
2. **Namespace isolation**: Each provider owns a namespace, preventing naming collisions.
3. **Conjunctive (AND) matching**: All required features must be satisfied.
4. **Disjunctive (OR) multi-value**: For features that accept multiple values, any one match suffices.
5. **Ordered preference**: Within each feature, values are ordered from most-preferred to least-preferred
   so the matcher can select the best-fitting device without provider-specific logic.

We adopt this 3-tuple format for describing accelerator device capabilities.
Each accelerator plugin acts as a **variant provider** that reports variant properties per device.
The Sokovan scheduler acts as the **matcher** that checks workload requirements against device properties.

```python
# ai.backend.common.accelerator
# ------------------------------
from __future__ import annotations

import enum
from typing import Optional, Sequence

import attrs


class VariantMatchMode(enum.StrEnum):
    """How a feature value should be matched against a requirement."""
    EXACT = "exact"         # value must be identical
    MINIMUM = "minimum"     # value must be >= the required value (semver/numeric comparison)
    COMPATIBLE = "compatible"  # value must be compatible (prefix matching like "12.x")


@attrs.define(frozen=True)
class VariantProperty:
    """A single accelerator capability expressed as a PEP-817-style 3-tuple.

    Serialized as: "{namespace}::{feature_name}::{feature_value}"
    """
    namespace: str       # e.g., "nvidia", "amd", "rebellions", "intel"
    feature_name: str    # e.g., "cuda_version", "compute_capability", "precision"
    feature_value: str   # e.g., "12.8", "9.0", "bf16"

    def __str__(self) -> str:
        return f"{self.namespace}::{self.feature_name}::{self.feature_value}"

    @classmethod
    def from_str(cls, s: str) -> VariantProperty:
        parts = s.split("::")
        if len(parts) != 3:
            raise ValueError(f"Invalid variant property format: {s!r}")
        return cls(namespace=parts[0], feature_name=parts[1], feature_value=parts[2])


@attrs.define(frozen=True)
class VariantFeatureDescriptor:
    """Describes a single feature within a namespace, including its match semantics.

    Analogous to PEP 817's VariantFeatureConfig, with Backend.AI-specific extensions
    for range-based matching.
    """
    name: str
    match_mode: VariantMatchMode = VariantMatchMode.EXACT
    multi_value: bool = False
    ordered_values: Sequence[str] = attrs.Factory(list)


@attrs.define(frozen=True)
class VariantNamespaceDescriptor:
    """Describes a variant namespace with its features and ordering metadata.

    Each accelerator plugin provides one of these per namespace it governs.
    """
    namespace: str
    features: Sequence[VariantFeatureDescriptor] = attrs.Factory(list)
```

### Example: NVIDIA CUDA Plugin Variant Properties

```python
# What the CUDA plugin reports per device (e.g., NVIDIA A100 80GB)
device_variant_properties = [
    VariantProperty("nvidia", "cuda_version", "12.8"),
    VariantProperty("nvidia", "compute_capability", "8.0"),
    VariantProperty("nvidia", "precision", "fp64"),
    VariantProperty("nvidia", "precision", "tf32"),
    VariantProperty("nvidia", "precision", "bf16"),
    VariantProperty("nvidia", "precision", "fp16"),
    VariantProperty("nvidia", "precision", "fp8"),
    VariantProperty("nvidia", "precision", "int8"),
    VariantProperty("nvidia", "memory_type", "hbm2e"),
    VariantProperty("nvidia", "partitioning", "mig"),
    VariantProperty("nvidia", "gpu_arch", "ampere"),
]

# The namespace descriptor that accompanies the above
nvidia_namespace = VariantNamespaceDescriptor(
    namespace="nvidia",
    features=[
        VariantFeatureDescriptor(
            name="cuda_version",
            match_mode=VariantMatchMode.MINIMUM,
            multi_value=False,
            ordered_values=["12.8", "12.6", "12.4", "12.2", "12.0", "11.8"],
        ),
        VariantFeatureDescriptor(
            name="compute_capability",
            match_mode=VariantMatchMode.MINIMUM,
            multi_value=False,
            ordered_values=["9.0", "8.9", "8.6", "8.0", "7.5", "7.0"],
        ),
        VariantFeatureDescriptor(
            name="precision",
            match_mode=VariantMatchMode.EXACT,
            multi_value=True,
            ordered_values=["fp64", "tf32", "bf16", "fp16", "fp8", "int8", "int4"],
        ),
        VariantFeatureDescriptor(
            name="memory_type",
            match_mode=VariantMatchMode.EXACT,
            multi_value=False,
            ordered_values=["hbm3", "hbm2e", "hbm2", "gddr6x", "gddr6"],
        ),
        VariantFeatureDescriptor(
            name="partitioning",
            match_mode=VariantMatchMode.EXACT,
            multi_value=True,
            ordered_values=["mig", "mps"],
        ),
        VariantFeatureDescriptor(
            name="gpu_arch",
            match_mode=VariantMatchMode.EXACT,
            multi_value=False,
            ordered_values=["blackwell", "hopper", "lovelace", "ampere", "turing", "volta"],
        ),
    ],
)
```

### Example: AMD ROCm Plugin Variant Properties

```python
# AMD Instinct MI300X
device_variant_properties = [
    VariantProperty("amd", "rocm_version", "6.3"),
    VariantProperty("amd", "gfx_arch", "gfx942"),
    VariantProperty("amd", "precision", "fp64"),
    VariantProperty("amd", "precision", "bf16"),
    VariantProperty("amd", "precision", "fp16"),
    VariantProperty("amd", "precision", "fp8"),
    VariantProperty("amd", "precision", "int8"),
    VariantProperty("amd", "memory_type", "hbm3"),
]

amd_namespace = VariantNamespaceDescriptor(
    namespace="amd",
    features=[
        VariantFeatureDescriptor(
            name="rocm_version",
            match_mode=VariantMatchMode.MINIMUM,
            multi_value=False,
            ordered_values=["6.3", "6.2", "6.1", "6.0", "5.7"],
        ),
        VariantFeatureDescriptor(
            name="gfx_arch",
            match_mode=VariantMatchMode.EXACT,
            multi_value=False,
            ordered_values=["gfx942", "gfx941", "gfx90a", "gfx908"],
        ),
        VariantFeatureDescriptor(
            name="precision",
            match_mode=VariantMatchMode.EXACT,
            multi_value=True,
            ordered_values=["fp64", "bf16", "fp16", "fp8", "int8"],
        ),
    ],
)
```

### Updated `AbstractComputeDevice`

```python
# ai.backend.agent.resources
# --------------------------
class AbstractComputeDevice:
    device_id: DeviceId
    hw_location: str          # either PCI bus ID or arbitrary string
    numa_node: Optional[int]  # NUMA node ID (None if not applicable)
    memory_size: int          # (legacy-compat) size of the on-device memory (bytes)
    processing_units: int     # (legacy-compat) number of the representative compute units
    memory_spec: MemorySpec   # (new) detailed memory specification
    compute_units: Sequence[ComputeUnit]  # (new) detailed compute unit specification
    precision_support: Sequence[ComputePrecisionSupport]
    partitioning_support: Sequence[PartitioningCapability]
    variant_properties: Sequence[VariantProperty]   # (new) PEP-817-style 3-tuple properties
```

### Variant Matching Algorithm

Following PEP 817's provider-independent matching principle, the matching logic checks
set membership without understanding individual provider semantics:

```python
# ai.backend.common.accelerator
# ------------------------------
from collections import defaultdict
from packaging.version import Version


def check_variant_compatibility(
    required: Sequence[VariantProperty],
    device_props: Sequence[VariantProperty],
    namespace_descriptors: Mapping[str, VariantNamespaceDescriptor],
) -> bool:
    """Check if a device's variant properties satisfy all requirements.

    This implements PEP 817-style conjunctive matching:
    - All required features must be satisfied (AND across features).
    - For multi-value features, any one match suffices (OR across values).
    - For MINIMUM match mode, the device value must be >= required value.
    """
    # Index device properties by (namespace, feature_name) -> set of values
    device_index: dict[tuple[str, str], set[str]] = defaultdict(set)
    for prop in device_props:
        device_index[(prop.namespace, prop.feature_name)].add(prop.feature_value)

    # Group requirements by (namespace, feature_name)
    req_index: dict[tuple[str, str], set[str]] = defaultdict(set)
    for prop in required:
        req_index[(prop.namespace, prop.feature_name)].add(prop.feature_value)

    for (ns, feat), req_values in req_index.items():
        device_values = device_index.get((ns, feat))
        if device_values is None:
            return False  # device does not report this feature at all

        # Determine match mode from namespace descriptor
        ns_desc = namespace_descriptors.get(ns)
        feat_desc = None
        if ns_desc:
            for fd in ns_desc.features:
                if fd.name == feat:
                    feat_desc = fd
                    break

        match_mode = feat_desc.match_mode if feat_desc else VariantMatchMode.EXACT
        is_multi = feat_desc.multi_value if feat_desc else False

        if match_mode == VariantMatchMode.MINIMUM:
            # For MINIMUM: device must have a value >= max of required values
            # (similar to PEP 817's cuda_version_lower_bound approach)
            max_required = max(req_values, key=_version_key)
            if not any(_version_key(dv) >= _version_key(max_required) for dv in device_values):
                return False

        elif match_mode == VariantMatchMode.COMPATIBLE:
            # Prefix-based compatibility (e.g., "12" matches "12.4", "12.8")
            if not any(
                any(dv.startswith(rv) or rv.startswith(dv) for dv in device_values)
                for rv in req_values
            ):
                return False

        else:  # EXACT
            if is_multi:
                # Multi-value: at least one required value must be in device values
                if not req_values & device_values:
                    return False
            else:
                # Single-value: the required value must match
                if not req_values & device_values:
                    return False

    return True


def _version_key(v: str) -> tuple[int, ...]:
    """Parse a version-like string into a comparable tuple."""
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)
```

### DB Schema: Device Variant Properties

Building on BEP-1047's `resource_slot_types` and `agent_resources` tables, we add
device-level variant property storage that the Manager can query directly.

```sql
-- Stores per-device variant properties reported by agents.
-- One row per (agent, device, variant property).
CREATE TABLE agent_device_variant_properties (
    agent_id     VARCHAR(64) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    device_name  VARCHAR(64) NOT NULL,    -- e.g., "cuda", "rocm"
    device_id    VARCHAR(64) NOT NULL,    -- plugin-specific device ID
    namespace    VARCHAR(64) NOT NULL,    -- variant namespace
    feature_name VARCHAR(64) NOT NULL,    -- variant feature name
    feature_value VARCHAR(128) NOT NULL,  -- variant feature value
    reported_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (agent_id, device_name, device_id, namespace, feature_name, feature_value)
);

-- Index for scheduler queries: "find agents that have devices supporting X"
CREATE INDEX ix_advp_ns_feat_val
    ON agent_device_variant_properties (namespace, feature_name, feature_value);

-- Index for resource group-scoped queries
-- (used with JOIN on agents.scaling_group)
CREATE INDEX ix_advp_agent_device
    ON agent_device_variant_properties (agent_id, device_name);
```

```python
# ai.backend.manager.models.agent_device
# ----------------------------------------
class AgentDeviceVariantPropertyRow(Base):
    __tablename__ = "agent_device_variant_properties"

    agent_id: Mapped[str] = mapped_column(
        sa.String(64),
        sa.ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    device_name: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    device_id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    namespace: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    feature_name: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    feature_value: Mapped[str] = mapped_column(sa.String(128), primary_key=True)
    reported_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
```

### Variant Namespace Descriptor Storage

Namespace descriptors are stored per agent (each agent reports what its plugins support)
and are used by the scheduler to interpret variant properties during matching.

```sql
-- Stores variant namespace descriptors reported by each agent's plugins.
CREATE TABLE agent_variant_namespace_descriptors (
    agent_id     VARCHAR(64) NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    namespace    VARCHAR(64) NOT NULL,
    descriptor   JSONB NOT NULL,     -- serialized VariantNamespaceDescriptor
    reported_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (agent_id, namespace)
);
```

```python
class AgentVariantNamespaceDescriptorRow(Base):
    __tablename__ = "agent_variant_namespace_descriptors"

    agent_id: Mapped[str] = mapped_column(
        sa.String(64),
        sa.ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    namespace: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    descriptor: Mapped[dict] = mapped_column(sa.JSON, nullable=False)
    reported_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
```

### Integration with BEP-1047

BEP-1047 Phase 1 created the `resource_slot_types` table for slot-level metadata
and `agent_resources` for per-agent, per-slot capacity/usage.
The new `agent_device_variant_properties` table extends this to **per-device** granularity:

```
resource_slot_types          — "what resource slot types exist?" (slot metadata registry)
     ↓
agent_resources              — "how much capacity does each agent have per slot?" (quantitative)
     ↓
agent_device_variant_properties — "what capabilities does each device have?" (qualitative)
```

BEP-1047's Open Question #3 ("Should `resource_slot_types` absorb BEP-1000's full schema?")
is resolved by **keeping them separate**: `resource_slot_types` stays as the slot-level registry,
while device-level qualitative metadata lives in `agent_device_variant_properties`.
The two are linked through the `device_name` column which corresponds to the slot name prefix
(e.g., device_name `"cuda"` maps to slots `"cuda.device"`, `"cuda.shares"`).

### Design Goals

* Generalize it for heterogeneous accelerators with multiple different partitioning support
* Support multiple different resource slot definitions from a single plugin instance (e.g,. MIG + fGPU mixed in a single node).
* Make it extensible without changing Python plugin interfaces, by using a comprehensive schema-based metadata interface using JSON.
* Consider defining an explicit jsonschema for easier validation.
* Unify a-little-bit duplicated interfaces, like: "get_metadata()" and "extra_info()".
* **NEW**: Enable the Manager/Scheduler to make device-capability-aware placement decisions using PEP-817-style variant properties.
* **NEW**: Support range-based matching (minimum version, compatible version) in addition to exact matching, following PEP 817's provider-controlled compatibility model.

### Accelerator API Redesign

Refer to [BEP-1016](BEP-1016-accelerator-interface-v2.md).
