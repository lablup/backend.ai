"""Common GraphQL types shared across multiple domains."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import strawberry

from ai.backend.common.types import ServicePortProtocols

# ========== Resource Options Types ==========


@strawberry.type(
    name="ResourceOptsEntry",
    description=(
        "Added in 26.1.0. A single key-value entry representing a resource option. "
        "Contains additional resource configuration such as shared memory settings."
    ),
)
class ResourceOptsEntryGQL:
    """Single resource option entry with name and value."""

    name: str = strawberry.field(description="The name of this resource option. Example: 'shmem'.")
    value: str = strawberry.field(description="The value for this resource option. Example: '64m'.")


@strawberry.type(
    name="ResourceOpts",
    description=(
        "Added in 26.1.0. A collection of additional resource options for a deployment. "
        "Contains key-value pairs for resource configuration like shared memory."
    ),
)
class ResourceOptsGQL:
    """Resource options containing multiple key-value entries."""

    entries: list[ResourceOptsEntryGQL] = strawberry.field(
        description="List of resource option entries. Each entry contains a key-value pair."
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
        "Added in 26.2.0. A single service port entry representing an exposed service. "
        "Contains port mapping and protocol information for accessing services."
    ),
)
class ServicePortEntryGQL:
    """Single service port entry with name, protocol, and port mappings."""

    name: str = strawberry.field(
        description="Name of the service (e.g., 'jupyter', 'tensorboard', 'ssh')."
    )
    protocol: ServicePortProtocols = strawberry.field(
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
            protocol=ServicePortProtocols(data["protocol"]),
            container_ports=list(data["container_ports"]),
            host_ports=list(data["host_ports"]),
            is_inference=data["is_inference"],
        )


@strawberry.type(
    name="ServicePorts",
    description=(
        "Added in 26.2.0. A collection of exposed service ports. "
        "Each entry defines a service accessible through the compute session."
    ),
)
class ServicePortsGQL:
    """Service ports containing multiple port entries."""

    entries: list[ServicePortEntryGQL] = strawberry.field(
        description="List of service port entries."
    )
