"""
Response DTOs for model serving (legacy service) system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, NonNegativeFloat, NonNegativeInt

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import RuntimeVariant

__all__ = (
    # Response models
    "SuccessResponseModel",
    "CompactServeInfoModel",
    "RouteInfoModel",
    "ServeInfoModel",
    "ServiceSearchItemModel",
    "PaginationInfoModel",
    "SearchServicesResponseModel",
    "TryStartResponseModel",
    "ScaleResponseModel",
    "TokenResponseModel",
    "ErrorInfoModel",
    "ErrorListResponseModel",
    "RuntimeInfo",
    "RuntimeInfoModel",
)


class SuccessResponseModel(BaseResponseModel):
    success: bool = Field(default=True)


class CompactServeInfoModel(BaseResponseModel):
    id: uuid.UUID = Field(description="Unique ID referencing the model service.")
    name: str = Field(description="Name of the model service.")
    replicas: NonNegativeInt = Field(description="Number of identical inference sessions.")
    desired_session_count: NonNegativeInt = Field(description="Deprecated; use `replicas` instead.")
    active_route_count: NonNegativeInt = Field(
        description=(
            "Information of routes which are actually spawned and ready to accept the traffic."
        )
    )
    service_endpoint: HttpUrl | None = Field(
        default=None,
        description=(
            "HTTP(S) endpoint to the API service. This field will be filed after the attempt to"
            " create a first inference session succeeds. Endpoint created is fixed and immutable"
            " for the bound endpoint until the endpoint is destroyed."
        ),
    )
    is_public: bool = Field(
        description=(
            'Indicates if the API endpoint is open to public. In this context "public" means'
            " there will be no authentication required to communicate with this API service."
        )
    )


class RouteInfoModel(BaseModel):
    route_id: uuid.UUID = Field(
        description=(
            "Unique ID referencing endpoint route. Each endpoint route has a one-to-one"
            " relationship with the inference session."
        )
    )
    session_id: uuid.UUID | None = Field(description="Unique ID referencing the inference session.")
    traffic_ratio: NonNegativeFloat


class ServeInfoModel(BaseResponseModel):
    model_config = ConfigDict(protected_namespaces=())

    endpoint_id: uuid.UUID = Field(description="Unique ID referencing the model service.")
    model_id: uuid.UUID = Field(description="ID of model VFolder.")
    extra_mounts: Sequence[uuid.UUID] = Field(
        description="List of extra VFolders which will be mounted to model service session."
    )
    name: str = Field(description="Name of the model service.")
    replicas: NonNegativeInt = Field(description="Number of identical inference sessions.")
    desired_session_count: NonNegativeInt = Field(description="Deprecated; use `replicas` instead.")
    model_definition_path: str | None = Field(
        description=(
            "Path to the the model definition file. If not set, Backend.AI will look for"
            " model-definition.yml or model-definition.yaml by default."
        )
    )
    active_routes: list[RouteInfoModel] = Field(
        description="Information of routes which are bound with healthy sessions."
    )
    service_endpoint: HttpUrl | None = Field(
        default=None,
        description=(
            "HTTP(S) endpoint to the API service. This field will be filed after the attempt to"
            " create a first inference session succeeds. Endpoint created is fixed and immutable"
            " for the bound endpoint until the endpoint is destroyed."
        ),
    )
    is_public: bool = Field(
        description=(
            'Indicates if the API endpoint is open to public. In this context "public" means'
            " there will be no authentication required to communicate with this API service."
        )
    )
    runtime_variant: RuntimeVariant = Field(
        description="Type of the inference runtime the image will try to load."
    )


class ServiceSearchItemModel(BaseResponseModel):
    id: uuid.UUID = Field(description="Service/endpoint UUID.")
    name: str = Field(description="Service name.")
    desired_session_count: NonNegativeInt = Field(description="Target replica count.")
    replicas: NonNegativeInt = Field(description="Target replica count.")
    active_route_count: NonNegativeInt = Field(
        description="Number of active routing entries (HEALTHY status)."
    )
    service_endpoint: HttpUrl | None = Field(
        default=None, description="Public URL of the service endpoint (nullable)."
    )
    resource_slots: dict[str, Any] = Field(description="Resource allocation per replica.")
    resource_group: str = Field(description="Name of the resource group for inference sessions.")
    open_to_public: bool = Field(description="Whether the endpoint is publicly accessible.")


class PaginationInfoModel(BaseResponseModel):
    total: int = Field(description="Total number of items matching the query.")
    offset: int = Field(description="Current offset.")
    limit: int = Field(description="Current limit.")


class SearchServicesResponseModel(BaseResponseModel):
    items: list[ServiceSearchItemModel]
    pagination: PaginationInfoModel


class TryStartResponseModel(BaseResponseModel):
    task_id: str


class ScaleResponseModel(BaseResponseModel):
    current_route_count: int
    target_count: int


class TokenResponseModel(BaseResponseModel):
    token: str


class ErrorInfoModel(BaseModel):
    session_id: uuid.UUID | None
    error: dict[str, Any]


class ErrorListResponseModel(BaseResponseModel):
    errors: list[ErrorInfoModel]
    retries: int


class RuntimeInfo(BaseModel):
    name: str = Field(description="Identifier to be passed later inside request body")
    human_readable_name: str = Field(description="Use this value as displayed label to user")


class RuntimeInfoModel(BaseResponseModel):
    runtimes: list[RuntimeInfo]
