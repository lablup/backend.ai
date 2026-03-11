"""Type definitions for WSProxy client."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ai.backend.common.config import ModelHealthCheck


class SessionTagsModel(BaseModel):
    """Session information for endpoint creation."""

    model_config = ConfigDict(populate_by_name=True)

    user_uuid: str
    group_id: str
    domain_name: str


class EndpointTagsModel(BaseModel):
    """Endpoint metadata for endpoint creation."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    runtime_variant: str
    existing_url: str | None = None


class TagsModel(BaseModel):
    """Combined tags for endpoint creation."""

    model_config = ConfigDict(populate_by_name=True)

    session: SessionTagsModel
    endpoint: EndpointTagsModel


class CreateEndpointRequestBody(BaseModel):
    """Request body for creating an endpoint in WSProxy."""

    model_config = ConfigDict(populate_by_name=True)

    version: str = Field(default="v2", description="API version")
    service_name: str = Field(description="Name of the service/endpoint")
    tags: TagsModel = Field(description="Metadata tags for the endpoint")
    apps: dict[str, Any] = Field(default_factory=dict, description="Application configuration")
    open_to_public: bool = Field(
        default=False, description="Whether the endpoint is publicly accessible"
    )
    health_check: ModelHealthCheck | None = Field(
        default=None, description="Health check configuration"
    )


class SyncRouteModel(BaseModel):
    """Model for a single route in sync request."""

    model_config = ConfigDict(populate_by_name=True)

    route_id: UUID
    session_id: UUID
    kernel_host: str | None = None
    kernel_port: int
    traffic_ratio: float = 1.0


class SyncRoutesRequestBody(BaseModel):
    """Request body for syncing routes to an endpoint in App Proxy."""

    model_config = ConfigDict(populate_by_name=True)

    routes: list[SyncRouteModel] = Field(description="List of routes to sync")
