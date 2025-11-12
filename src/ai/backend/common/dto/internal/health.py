from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ComponentHealthStatus(BaseModel):
    """
    Health status of a single component (for API response).

    This is used in external API responses (/health endpoint).
    """

    service_group: str = Field(
        description="The service group category (e.g., manager, database, redis, etcd)"
    )
    component_id: str = Field(description="Unique identifier for the component")
    is_healthy: bool = Field(description="Whether the component is currently healthy")
    last_checked_at: datetime = Field(description="Timestamp when the health check was performed")
    error_message: Optional[str] = Field(
        default=None, description="Error message if the health check failed"
    )


class HealthCheckResponse(BaseModel):
    """
    Overall health check response containing all component statuses.

    This is the top-level response model for the /health API endpoint.
    """

    overall_healthy: bool = Field(description="Whether all registered components are healthy")
    components: list[ComponentHealthStatus] = Field(
        description="Health status of each registered component"
    )
    timestamp: datetime = Field(description="Timestamp when this response was generated")
