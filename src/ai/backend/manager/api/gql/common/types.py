"""Common GraphQL types shared across multiple domains."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

import strawberry

from ai.backend.common.dto.manager.v2.resource_slot.types import (
    ResourceOptsDTOInput,
    ResourceOptsEntryDTO,
    ResourceOptsInfoDTO,
)
from ai.backend.common.dto.manager.v2.streaming.types import ServiceProtocol
from ai.backend.common.types import (
    ClusterMode,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_output_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

# ========== Common Enums ==========


@strawberry.enum(
    name="ClusterMode",
    description="Added in 25.19.0. Cluster mode for compute sessions and deployments.",
)
class ClusterModeGQL(StrEnum):
    """GraphQL enum for cluster mode."""

    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"

    @classmethod
    def from_internal(cls, internal: ClusterMode) -> ClusterModeGQL:
        """Convert internal ClusterMode to GraphQL enum."""
        match internal:
            case ClusterMode.SINGLE_NODE:
                return cls.SINGLE_NODE
            case ClusterMode.MULTI_NODE:
                return cls.MULTI_NODE

    def to_internal(self) -> ClusterMode:
        """Convert GraphQL enum to internal ClusterMode."""
        match self:
            case ClusterModeGQL.SINGLE_NODE:
                return ClusterMode.SINGLE_NODE
            case ClusterModeGQL.MULTI_NODE:
                return ClusterMode.MULTI_NODE


@strawberry.enum(
    name="SessionV2Type",
    description="Added in 26.3.0. Type of compute session.",
)
class SessionV2TypeGQL(StrEnum):
    """GraphQL enum for session types."""

    INTERACTIVE = "interactive"
    BATCH = "batch"
    INFERENCE = "inference"
    SYSTEM = "system"

    @classmethod
    def from_internal(cls, internal: SessionTypes) -> SessionV2TypeGQL:
        """Convert internal SessionTypes to GraphQL enum."""
        match internal:
            case SessionTypes.INTERACTIVE:
                return cls.INTERACTIVE
            case SessionTypes.BATCH:
                return cls.BATCH
            case SessionTypes.INFERENCE:
                return cls.INFERENCE
            case SessionTypes.SYSTEM:
                return cls.SYSTEM

    def to_internal(self) -> SessionTypes:
        """Convert GraphQL enum to internal SessionTypes."""
        match self:
            case SessionV2TypeGQL.INTERACTIVE:
                return SessionTypes.INTERACTIVE
            case SessionV2TypeGQL.BATCH:
                return SessionTypes.BATCH
            case SessionV2TypeGQL.INFERENCE:
                return SessionTypes.INFERENCE
            case SessionV2TypeGQL.SYSTEM:
                return SessionTypes.SYSTEM


@strawberry.enum(
    name="SessionV2Result",
    description=(
        "Added in 26.3.0. Result status of a session or kernel execution. "
        "Indicates the final outcome after the session/kernel has terminated. "
        "UNDEFINED: The session has not yet finished or its result is unknown. "
        "SUCCESS: The session completed normally without errors. "
        "FAILURE: The session terminated abnormally due to an error or user cancellation."
    ),
)
class SessionV2ResultGQL(StrEnum):
    """GraphQL enum for session result.

    Represents the final outcome of a session or kernel execution.
    Used in lifecycle info fields to indicate how the workload finished.
    """

    UNDEFINED = "undefined"
    SUCCESS = "success"
    FAILURE = "failure"

    @classmethod
    def from_internal(cls, internal: SessionResult) -> SessionV2ResultGQL:
        """Convert internal SessionResult to GraphQL enum."""
        match internal:
            case SessionResult.UNDEFINED:
                return cls.UNDEFINED
            case SessionResult.SUCCESS:
                return cls.SUCCESS
            case SessionResult.FAILURE:
                return cls.FAILURE

    def to_internal(self) -> SessionResult:
        """Convert GraphQL enum to internal SessionResult."""
        match self:
            case SessionV2ResultGQL.UNDEFINED:
                return SessionResult.UNDEFINED
            case SessionV2ResultGQL.SUCCESS:
                return SessionResult.SUCCESS
            case SessionV2ResultGQL.FAILURE:
                return SessionResult.FAILURE


ServicePortProtocolGQL: type[ServiceProtocol] = strawberry.enum(
    ServiceProtocol,
    name="ServicePortProtocol",
    description="Added in 26.2.0. Protocol type for service ports.",
)


# ========== Resource Options Types ==========


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A single key-value entry representing a resource option. "
            "Contains additional resource configuration such as shared memory settings."
        ),
    ),
    name="ResourceOptsEntry",
)
class ResourceOptsEntryGQL:
    """Single resource option entry with name and value."""

    name: str = strawberry.field(description="The name of this resource option. Example: 'shmem'.")
    value: str = strawberry.field(description="The value for this resource option. Example: '64m'.")


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A collection of additional resource options for a deployment. "
            "Contains key-value pairs for resource configuration like shared memory."
        ),
    ),
    name="ResourceOpts",
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

    @classmethod
    def from_pydantic(cls, dto: ResourceOptsInfoDTO) -> ResourceOptsGQL:
        """Convert a ResourceOptsInfoDTO to GQL type."""
        return cls(entries=[ResourceOptsEntryGQL(name=e.name, value=e.value) for e in dto.entries])


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A single key-value entry representing a resource option.",
        added_version="26.1.0",
    ),
    name="ResourceOptsEntryInput",
)
class ResourceOptsEntryInput(PydanticInputMixin[ResourceOptsEntryDTO]):
    """Single resource option entry input with name and value."""

    name: str = strawberry.field(description="The name of this resource option (e.g., 'shmem').")
    value: str = strawberry.field(description="The value for this resource option (e.g., '64m').")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A collection of additional resource options for input.", added_version="26.1.0"
    ),
    name="ResourceOptsInput",
)
class ResourceOptsInput(PydanticInputMixin[ResourceOptsDTOInput]):
    """Resource options input containing multiple key-value entries."""

    entries: list[ResourceOptsEntryInput] = strawberry.field(
        description="List of resource option entries."
    )


# ========== Service Port Types ==========


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "A single service port entry representing an exposed service. "
            "Contains port mapping and protocol information for accessing services."
        ),
    ),
    name="ServicePortEntry",
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


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "A collection of exposed service ports. "
            "Each entry defines a service accessible through the compute session."
        ),
    ),
    name="ServicePorts",
)
class ServicePortsGQL:
    """Service ports containing multiple port entries."""

    entries: list[ServicePortEntryGQL] = strawberry.field(
        description="List of service port entries."
    )
