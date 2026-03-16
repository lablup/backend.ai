"""
Response DTOs for Model Serving DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.model_serving.types import RouteInfoSummary, RuntimeVariant

__all__ = (
    "CompactServiceNode",
    "CreateServicePayload",
    "DeleteServicePayload",
    "GenerateTokenPayload",
    "ScaleServicePayload",
    "ServiceNode",
    "UpdateServicePayload",
)


class ServiceNode(BaseResponseModel):
    """Node model representing a model serving service entity."""

    id: UUID = Field(description="Service ID")
    name: str = Field(description="Service name")
    replicas: int = Field(description="Number of replicas")
    active_route_count: int = Field(description="Number of active routes")
    service_endpoint: str | None = Field(default=None, description="Service endpoint URL")
    is_public: bool = Field(description="Whether the service is open to public")
    runtime_variant: RuntimeVariant = Field(description="Runtime variant used by the service")
    model_id: UUID | None = Field(default=None, description="Model vfolder ID")
    model_definition_path: str | None = Field(
        default=None, description="Path to the model definition file"
    )
    active_routes: list[RouteInfoSummary] = Field(
        default_factory=list, description="List of active route summaries"
    )


class CompactServiceNode(BaseResponseModel):
    """Compact node model representing a model serving service (without route details)."""

    id: UUID = Field(description="Service ID")
    name: str = Field(description="Service name")
    replicas: int = Field(description="Number of replicas")
    active_route_count: int = Field(description="Number of active routes")
    service_endpoint: str | None = Field(default=None, description="Service endpoint URL")
    is_public: bool = Field(description="Whether the service is open to public")


class CreateServicePayload(BaseResponseModel):
    """Payload for service creation mutation result."""

    service: ServiceNode = Field(description="Created service")


class UpdateServicePayload(BaseResponseModel):
    """Payload for service update mutation result."""

    service: ServiceNode = Field(description="Updated service")


class DeleteServicePayload(BaseResponseModel):
    """Payload for service deletion mutation result."""

    id: UUID = Field(description="ID of the deleted service")
    success: bool = Field(description="Whether the deletion succeeded")


class ScaleServicePayload(BaseResponseModel):
    """Payload for service scale mutation result."""

    current_route_count: int = Field(description="Current number of active routes")
    target_count: int = Field(description="Target replica count after scaling")


class GenerateTokenPayload(BaseResponseModel):
    """Payload for token generation mutation result."""

    token: str = Field(description="Generated authentication token")
