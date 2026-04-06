from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    """Health status enumeration for components."""

    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class SubComponentConnectivityStatus(BaseModel):
    """
    Connectivity status of a sub-component (e.g., operation or monitor client).

    Used when a component has internal sub-components with independent health,
    such as Valkey's operation and monitor clients.
    """

    is_healthy: bool = Field(description="Whether the sub-component is currently healthy")
    last_checked_at: datetime = Field(description="Timestamp when the health check was performed")
    error_message: str | None = Field(
        default=None, description="Error message if the health check failed"
    )


class ComponentConnectivityStatus(BaseModel):
    """
    Connectivity status of a single component (for API response).

    This is used in external API responses (/health endpoint).
    """

    service_group: str = Field(
        description="The service group category (e.g., manager, database, redis, etcd)"
    )
    component_id: str = Field(description="Unique identifier for the component")
    is_healthy: bool = Field(description="Whether the component is currently healthy")
    last_checked_at: datetime = Field(description="Timestamp when the health check was performed")
    error_message: str | None = Field(
        default=None, description="Error message if the health check failed"
    )
    sub_components: dict[str, SubComponentConnectivityStatus] | None = Field(
        default=None,
        description="Health status of internal sub-components (e.g., operation and monitor clients)",
    )


class ConnectivityCheckResponse(BaseModel):
    """
    Connectivity check response containing status of all registered components.

    This is embedded in the main HealthResponse.
    """

    overall_healthy: bool = Field(description="Whether all registered components are healthy")
    connectivity_checks: list[ComponentConnectivityStatus] = Field(
        description="Connectivity check results for each registered component"
    )
    timestamp: datetime = Field(description="Timestamp when this response was generated")


class HealthResponse(BaseModel):
    """
    Standard health check response for all Backend.AI components.

    This response includes basic service status information along with
    detailed connectivity status for all external dependencies.
    """

    status: HealthStatus = Field(description="Overall service status")
    version: str = Field(description="Version of the component")
    component: str = Field(
        description="Component name (e.g., 'agent', 'manager', 'storage-proxy', 'webserver', 'appproxy-coordinator', 'appproxy-worker')"
    )
    connectivity: ConnectivityCheckResponse = Field(
        description="Connectivity check results for external dependencies"
    )
