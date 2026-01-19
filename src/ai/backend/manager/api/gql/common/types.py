"""Common GraphQL types shared across multiple domains."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import strawberry

from ai.backend.common.types import (
    MountPermission,
    ServicePortProtocols,
    SessionResult,
    SessionTypes,
    VFolderUsageMode,
)

# ========== Common Enums ==========


SessionTypesGQL = strawberry.enum(
    SessionTypes,
    name="SessionType",
    description="Added in 26.1.0. Type of compute session.",
)

SessionResultGQL = strawberry.enum(
    SessionResult,
    name="SessionResult",
    description="Added in 26.1.0. Result status of a session execution.",
)

MountPermissionGQL = strawberry.enum(
    MountPermission,
    name="MountPermission",
    description="Added in 26.1.0. Permission level for virtual folder mounts.",
)

VFolderUsageModeGQL = strawberry.enum(
    VFolderUsageMode,
    name="VFolderUsageMode",
    description="Added in 26.1.0. Usage mode of a virtual folder.",
)

ServicePortProtocolGQL = strawberry.enum(
    ServicePortProtocols,
    name="ServicePortProtocol",
    description="Added in 26.1.0. Protocol types for service ports.",
)


# ========== Resource Options Types ==========


@strawberry.type(
    name="ResourceOptsEntry",
    description=(
        "Added in 26.1.0. A single resource option entry with name and value. "
        "Resource options provide additional configuration like shared memory settings."
    ),
)
class ResourceOptsEntryGQL:
    """Single resource option entry with name and value."""

    name: str = strawberry.field(description="The name of this resource option (e.g., 'shmem').")
    value: str = strawberry.field(description="The value for this resource option (e.g., '64m').")


@strawberry.type(
    name="ResourceOpts",
    description=(
        "Added in 26.1.0. A collection of additional resource options. "
        "Contains configuration like shared memory and other resource-specific settings."
    ),
)
class ResourceOptsGQL:
    """Resource options containing multiple entries."""

    entries: list[ResourceOptsEntryGQL] = strawberry.field(
        description="List of resource option entries."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> ResourceOptsGQL | None:
        """Convert a Mapping to GraphQL type."""
        if data is None:
            return None
        entries = [ResourceOptsEntryGQL(name=k, value=str(v)) for k, v in data.items()]
        return cls(entries=entries)


@strawberry.input(
    description="Added in 26.1.0. A single key-value entry representing a resource option."
)
class ResourceOptsEntryInput:
    """Single resource option entry input with name and value."""

    name: str = strawberry.field(description="The name of this resource option (e.g., 'shmem').")
    value: str = strawberry.field(description="The value for this resource option (e.g., '64m').")


@strawberry.input(
    description="Added in 26.1.0. A collection of additional resource options for input."
)
class ResourceOptsInput:
    """Resource options input containing multiple key-value entries."""

    entries: list[ResourceOptsEntryInput] = strawberry.field(
        description="List of resource option entries."
    )


# ========== Service Port Types ==========


@strawberry.type(
    name="ServicePortEntry",
    description=(
        "Added in 26.1.0. A single service port entry representing an exposed service. "
        "Contains port mapping and protocol information for accessing services."
    ),
)
class ServicePortEntryGQL:
    """Single service port entry with name, protocol, and port mappings."""

    name: str = strawberry.field(
        description="Name of the service (e.g., 'jupyter', 'tensorboard', 'ssh')."
    )
    protocol: ServicePortProtocolGQL = strawberry.field(
        description="Protocol type for this service port (http, tcp, preopen, internal)."
    )
    container_ports: list[int] = strawberry.field(description="Port numbers inside the container.")
    host_ports: list[int | None] = strawberry.field(
        description="Mapped port numbers on the host. May be null if not yet assigned."
    )
    is_inference: bool = strawberry.field(
        description="Whether this port is used for inference endpoints."
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServicePortEntryGQL:
        """Convert a dict to ServicePortEntryGQL."""
        return cls(
            name=data["name"],
            protocol=ServicePortProtocolGQL(data["protocol"]),
            container_ports=list(data["container_ports"]),
            host_ports=list(data["host_ports"]),
            is_inference=data["is_inference"],
        )


@strawberry.type(
    name="ServicePorts",
    description=(
        "Added in 26.1.0. A collection of exposed service ports. "
        "Each entry defines a service accessible through the compute session."
    ),
)
class ServicePortsGQL:
    """Service ports containing multiple port entries."""

    entries: list[ServicePortEntryGQL] = strawberry.field(
        description="List of service port entries."
    )


# ========== Status Error and Scheduler Types ==========


@strawberry.type(
    name="SchedulerPredicate",
    description=(
        "Added in 26.1.0. A scheduler predicate result from scheduling attempts. "
        "Predicates are conditions checked during session scheduling."
    ),
)
class SchedulerPredicateGQL:
    """A scheduler predicate entry."""

    name: str = strawberry.field(
        description="Name of the predicate (e.g., 'concurrency', 'reserved_time')."
    )
    msg: str | None = strawberry.field(
        description="Message explaining why the predicate failed. Null for passed predicates."
    )


@strawberry.type(
    name="SchedulerInfo",
    description=(
        "Added in 26.1.0. Scheduler information including retry attempts and predicate results. "
        "Contains details about scheduling attempts when a session is pending."
    ),
)
class SchedulerInfoGQL:
    """Scheduler information in status_data."""

    retries: int | None = strawberry.field(
        description="Number of scheduling attempts made for this session."
    )
    last_try: str | None = strawberry.field(
        description="ISO 8601 timestamp of the last scheduling attempt."
    )
    msg: str | None = strawberry.field(description="Message from the last scheduling attempt.")
    failed_predicates: list[SchedulerPredicateGQL] | None = strawberry.field(
        description="List of predicates that failed during scheduling."
    )
    passed_predicates: list[SchedulerPredicateGQL] | None = strawberry.field(
        description="List of predicates that passed during scheduling."
    )


# ========== Metric Types ==========


@strawberry.type(
    name="MetricStat",
    description=(
        "Added in 26.1.0. Statistical aggregation values for a metric over time. "
        "Contains min, max, sum, average, difference, and rate calculations."
    ),
)
class MetricStatGQL:
    """Statistical values for a metric."""

    min: str | None = strawberry.field(description="Minimum observed value.")
    max: str | None = strawberry.field(description="Maximum observed value.")
    sum: str | None = strawberry.field(description="Sum of all observed values.")
    avg: str | None = strawberry.field(description="Average of observed values.")
    diff: str | None = strawberry.field(description="Difference from previous measurement.")
    rate: str | None = strawberry.field(description="Rate of change per second.")


@strawberry.type(
    name="MetricValue",
    description=(
        "Added in 26.1.0. A metric measurement with current value, capacity, and statistics. "
        "Used for resource utilization metrics like CPU, memory, and I/O."
    ),
)
class MetricValueGQL:
    """A single metric measurement."""

    current: str = strawberry.field(description="Current measured value.")
    capacity: str | None = strawberry.field(
        description="Maximum capacity for this metric. Null for unbounded metrics."
    )
    pct: str | None = strawberry.field(
        description="Percentage utilization (current/capacity * 100)."
    )
    unit_hint: str | None = strawberry.field(
        description="Unit hint for display (e.g., 'bytes', 'msec', 'percent')."
    )
    stats: MetricStatGQL | None = strawberry.field(
        description="Statistical aggregation values over time."
    )


# ========== VFolder Mount Types ==========


@strawberry.type(
    name="VFolderMount",
    description=(
        "Added in 26.1.0. Information about a mounted virtual folder. "
        "Contains mount path, permissions, and usage mode details."
    ),
)
class VFolderMountGQL:
    """Virtual folder mount information."""

    name: str = strawberry.field(description="Name of the virtual folder.")
    vfid: str = strawberry.field(description="Unique identifier of the virtual folder.")
    vfsubpath: str = strawberry.field(description="Subpath within the virtual folder to mount.")
    host_path: str = strawberry.field(
        description="Path on the host where the virtual folder is stored."
    )
    kernel_path: str = strawberry.field(
        description="Path inside the container where the folder is mounted."
    )
    mount_perm: MountPermissionGQL = strawberry.field(
        description="Permission level for this mount (ro, rw, wd)."
    )
    usage_mode: VFolderUsageModeGQL = strawberry.field(
        description="Usage mode of the virtual folder (general, model, data)."
    )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VFolderMountGQL:
        """Convert a dict to VFolderMountGQL."""
        return cls(
            name=data["name"],
            vfid=str(data["vfid"]),
            vfsubpath=str(data["vfsubpath"]),
            host_path=str(data["host_path"]),
            kernel_path=str(data["kernel_path"]),
            mount_perm=MountPermissionGQL(data["mount_perm"]),
            usage_mode=VFolderUsageModeGQL(data["usage_mode"]),
        )


# ========== Internal Data Types ==========


@strawberry.type(
    name="DotfileInfo",
    description="Added in 26.1.0. Information about a dotfile to be provisioned in a container.",
)
class DotfileInfoGQL:
    path: str = strawberry.field(
        description="The file path where the dotfile will be placed (relative or absolute)."
    )
    data: str = strawberry.field(description="The content of the dotfile.")
    perm: str = strawberry.field(
        description="The file permission in octal string format (e.g., '0644')."
    )


@strawberry.type(
    name="SSHKeypair",
    description="Added in 26.1.0. SSH keypair for secure access.",
)
class SSHKeypairGQL:
    public_key: str = strawberry.field(description="The public key in OpenSSH format.")
    private_key: str = strawberry.field(description="The private key in PEM format.")
