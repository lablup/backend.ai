from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
from ai.backend.common.types import ServiceDiscoveryType

__all__ = (
    "ServiceDiscoveryConfig",
    "ServiceEndpointConfig",
)


class ServiceEndpointConfig(BaseConfigSchema):
    """Configuration for a single service endpoint.

    Describes how a specific service endpoint can be reached,
    including its role, network scope, address, and protocol.
    """

    role: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Role of this endpoint (e.g., 'main', 'health', 'internal').",
            added_version="26.3.0",
            example=ConfigExample(local="main", prod="main"),
        ),
    ]
    scope: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Network scope of this endpoint (e.g., 'public', 'private', 'internal').",
            added_version="26.3.0",
            example=ConfigExample(local="private", prod="public"),
        ),
    ]
    address: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Hostname or IP address of the endpoint.",
            added_version="26.3.0",
            example=ConfigExample(local="127.0.0.1", prod="manager.example.com"),
        ),
    ]
    port: Annotated[
        int,
        Field(),
        BackendAIConfigMeta(
            description="Port number of the endpoint.",
            added_version="26.3.0",
            example=ConfigExample(local=8080, prod=443),
        ),
    ]
    protocol: Annotated[
        str,
        Field(),
        BackendAIConfigMeta(
            description="Protocol used by the endpoint (e.g., 'grpc', 'http', 'https').",
            added_version="26.3.0",
            example=ConfigExample(local="http", prod="https"),
        ),
    ]
    metadata: Annotated[
        dict[str, str],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description="Additional metadata for the endpoint.",
            added_version="26.3.0",
            composite=CompositeType.DICT,
        ),
    ]


class ServiceDiscoveryConfig(BaseConfigSchema):
    """Configuration for service discovery mechanism.

    Service discovery allows Backend.AI components to locate and communicate
    with each other in a distributed environment.
    """

    type: Annotated[
        ServiceDiscoveryType,
        Field(default=ServiceDiscoveryType.REDIS),
        BackendAIConfigMeta(
            description=(
                "Type of service discovery to use. Supported types are 'etcd' and 'redis'."
            ),
            added_version="25.9.0",
            example=ConfigExample(local="redis", prod="redis"),
        ),
    ]
    instance_id: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Unique instance identifier for this service instance.",
            added_version="26.3.0",
        ),
    ]
    service_group: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Logical group name for this service (e.g., 'manager', 'agent', 'storage-proxy').",
            added_version="26.3.0",
        ),
    ]
    display_name: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Human-readable display name for this service instance.",
            added_version="26.3.0",
        ),
    ]
    extra_labels: Annotated[
        dict[str, str],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description="Additional labels for service categorization and filtering.",
            added_version="26.3.0",
            composite=CompositeType.DICT,
        ),
    ]
    endpoints: Annotated[
        list[ServiceEndpointConfig],
        Field(default_factory=list),
        BackendAIConfigMeta(
            description="List of endpoints exposed by this service instance.",
            added_version="26.3.0",
            composite=CompositeType.LIST,
        ),
    ]
