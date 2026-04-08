"""
Request DTOs for Model Serving DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.types import RuntimeVariant

__all__ = (
    "CreateServiceInput",
    "DeleteServiceInput",
    "GenerateTokenInput",
    "ScaleServiceInput",
    "ServiceConfigInput",
    "UpdateServiceInput",
)


class ServiceConfigInput(BaseRequestModel):
    """Input for model service configuration."""

    model_config = ConfigDict(protected_namespaces=())

    model: str = Field(description="Name or ID of the model VFolder")
    model_definition_path: str | None = Field(
        default=None,
        description="Path to the model definition file",
    )
    model_mount_destination: str = Field(
        default="/models",
        description="Mount destination for the model VFolder inside the inference session",
    )
    extra_mounts: dict[UUID, Any] = Field(
        default_factory=dict,
        description="Extra VFolders mounted to model service session",
    )
    environ: dict[str, str] | None = Field(
        default=None,
        description="Environment variables to be set inside the inference session",
    )
    scaling_group: str = Field(
        description="Name of the resource group to spawn inference sessions",
    )
    resources: dict[str, str | int] | None = Field(
        default=None,
        description="Resource requirements for the inference session",
    )
    resource_opts: dict[str, str | int | bool] = Field(
        default_factory=dict,
        description="Optional resource options",
    )


class CreateServiceInput(BaseRequestModel):
    """Input for creating a model service."""

    model_config = ConfigDict(protected_namespaces=())

    service_name: str = Field(
        min_length=4,
        max_length=64,
        pattern=r"^\w[\w-]*\w$",
        description="Name of the service",
    )
    image: str | None = Field(
        default=None,
        description="String reference of the image to create inference sessions",
    )
    architecture: str | None = Field(
        default=None,
        description="Image architecture",
    )
    group_name: str = Field(
        default="default",
        description="Name of the project to spawn sessions",
    )
    domain_name: str = Field(
        default="default",
        description="Name of the domain to spawn sessions",
    )
    replicas: int = Field(
        ge=1,
        description="Number of sessions to serve traffic",
    )
    runtime_variant: RuntimeVariant = Field(
        default=RuntimeVariant("custom"),
        description="Type of the inference runtime",
    )
    cluster_size: int = Field(
        default=1,
        description="Cluster size for the inference session",
    )
    cluster_mode: str = Field(
        default="SINGLE_NODE",
        description="Cluster mode for the inference session",
    )
    open_to_public: bool = Field(
        default=False,
        description="If true, do not require an API key to access the model service",
    )
    config: ServiceConfigInput = Field(description="Service configuration")

    @field_validator("service_name")
    @classmethod
    def service_name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("service_name must not be blank or whitespace-only")
        return stripped


class UpdateServiceInput(BaseRequestModel):
    """Input for updating a model service."""

    name: str | None = Field(default=None, description="Updated service name")
    replicas: int | None = Field(default=None, ge=0, description="Updated replica count")


class DeleteServiceInput(BaseRequestModel):
    """Input for deleting a model service."""

    id: UUID = Field(description="Service ID to delete")


class ScaleServiceInput(BaseRequestModel):
    """Input for scaling a model service."""

    to: int = Field(ge=0, description="Target number of inference sessions")


class GenerateTokenInput(BaseRequestModel):
    """Input for generating an access token for a model service."""

    duration: str | None = Field(
        default=None,
        description="The lifetime duration of the token",
    )
    valid_until: int | None = Field(
        default=None,
        description="The absolute token expiry date in Unix epoch format",
    )
