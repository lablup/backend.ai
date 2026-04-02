"""Common GraphQL types shared across multiple domains."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.resource_slot.types import (
    ResourceOptsDTOInput,
    ResourceOptsEntryDTO,
    ResourceOptsEntryInfoDTO,
    ResourceOptsInfoDTO,
    ServicePortEntryInfoDTO,
    ServicePortsInfoDTO,
)
from ai.backend.common.dto.manager.v2.streaming.types import ServiceProtocol
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

# ========== Common Enums ==========


@gql_enum(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="Cluster mode for compute sessions and deployments.",
    ),
    name="ClusterMode",
)
class ClusterModeGQL(StrEnum):
    """GraphQL enum for cluster mode."""

    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"


@gql_enum(
    BackendAIGQLMeta(added_version="26.3.0", description="Type of compute session."),
    name="SessionV2Type",
)
class SessionV2TypeGQL(StrEnum):
    """GraphQL enum for session types."""

    INTERACTIVE = "interactive"
    BATCH = "batch"
    INFERENCE = "inference"
    SYSTEM = "system"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description=(
            "Result status of a session or kernel execution. "
            "Indicates the final outcome after the session/kernel has terminated. "
            "UNDEFINED: The session has not yet finished or its result is unknown. "
            "SUCCESS: The session completed normally without errors. "
            "FAILURE: The session terminated abnormally due to an error or user cancellation."
        ),
    ),
    name="SessionV2Result",
)
class SessionV2ResultGQL(StrEnum):
    """GraphQL enum for session result.

    Represents the final outcome of a session or kernel execution.
    Used in lifecycle info fields to indicate how the workload finished.
    """

    UNDEFINED = "undefined"
    SUCCESS = "success"
    FAILURE = "failure"


ServicePortProtocolGQL: type[ServiceProtocol] = gql_enum(
    BackendAIGQLMeta(added_version="26.2.0", description="Protocol type for service ports."),
    ServiceProtocol,
    name="ServicePortProtocol",
)


# ========== Resource Options Types ==========


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A single key-value entry representing a resource option. "
            "Contains additional resource configuration such as shared memory settings."
        ),
    ),
    model=ResourceOptsEntryInfoDTO,
    name="ResourceOptsEntry",
)
class ResourceOptsEntryGQL(PydanticOutputMixin[ResourceOptsEntryInfoDTO]):
    """Single resource option entry with name and value."""

    name: str = gql_field(description="The name of this resource option. Example: 'shmem'.")
    value: str = gql_field(description="The value for this resource option. Example: '64m'.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A collection of additional resource options for a deployment. "
            "Contains key-value pairs for resource configuration like shared memory."
        ),
    ),
    model=ResourceOptsInfoDTO,
    name="ResourceOpts",
)
class ResourceOptsGQL(PydanticOutputMixin[ResourceOptsInfoDTO]):
    """Resource options containing multiple key-value entries."""

    entries: list[ResourceOptsEntryGQL] = gql_field(
        description="List of resource option entries. Each entry contains a key-value pair."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A single key-value entry representing a resource option.",
        added_version="26.1.0",
    ),
    name="ResourceOptsEntryInput",
)
class ResourceOptsEntryInput(PydanticInputMixin[ResourceOptsEntryDTO]):
    """Single resource option entry input with name and value."""

    name: str = gql_field(description="The name of this resource option (e.g., 'shmem').")
    value: str = gql_field(description="The value for this resource option (e.g., '64m').")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="A collection of additional resource options for input.", added_version="26.1.0"
    ),
    name="ResourceOptsInput",
)
class ResourceOptsInput(PydanticInputMixin[ResourceOptsDTOInput]):
    """Resource options input containing multiple key-value entries."""

    entries: list[ResourceOptsEntryInput] = gql_field(
        description="List of resource option entries."
    )


# ========== Service Port Types ==========


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "A single service port entry representing an exposed service. "
            "Contains port mapping and protocol information for accessing services."
        ),
    ),
    model=ServicePortEntryInfoDTO,
    name="ServicePortEntry",
)
class ServicePortEntryGQL(PydanticOutputMixin[ServicePortEntryInfoDTO]):
    """Single service port entry with name, protocol, and port mappings."""

    name: str = gql_field(
        description="Name of the service (e.g., 'jupyter', 'tensorboard', 'ssh')."
    )
    protocol: ServicePortProtocolGQL = gql_field(
        description="Protocol type for this service port (http, tcp, preopen, internal)."
    )
    container_ports: list[int] = gql_field(description="Port numbers inside the container.")
    host_ports: list[int | None] = gql_field(
        description="Mapped port numbers on the host. May be null if not yet assigned."
    )
    is_inference: bool = gql_field(description="Whether this port is used for inference endpoints.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "A collection of exposed service ports. "
            "Each entry defines a service accessible through the compute session."
        ),
    ),
    model=ServicePortsInfoDTO,
    name="ServicePorts",
)
class ServicePortsGQL(PydanticOutputMixin[ServicePortsInfoDTO]):
    """Service ports containing multiple port entries."""

    entries: list[ServicePortEntryGQL] = gql_field(description="List of service port entries.")
