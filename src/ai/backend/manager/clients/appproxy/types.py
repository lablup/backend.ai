"""Type definitions for WSProxy client."""

from __future__ import annotations

from typing import Optional

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
    existing_url: Optional[str] = None


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
    apps: dict = Field(default_factory=dict, description="Application configuration")
    open_to_public: bool = Field(
        default=False, description="Whether the endpoint is publicly accessible"
    )
    health_check: Optional[ModelHealthCheck] = Field(
        default=None, description="Health check configuration"
    )
