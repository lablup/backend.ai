"""
Request DTOs for model serving (legacy service) system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Self

from pydantic import (
    AliasChoices,
    AnyUrl,
    ConfigDict,
    Field,
    NonNegativeFloat,
    model_validator,
)

from ai.backend.common import typed_validators as tv
from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import RuntimeVariant

__all__ = (
    # Request models
    "ListServeRequestModel",
    "ServiceFilterModel",
    "SearchServicesRequestModel",
    "ServiceConfigModel",
    "NewServiceRequestModel",
    "ScaleRequestModel",
    "UpdateRouteRequestModel",
    "TokenRequestModel",
)


class ListServeRequestModel(BaseRequestModel):
    name: str | None = Field(default=None)


class ServiceFilterModel(BaseRequestModel):
    name: StringFilter | None = Field(default=None, description="Filter by service name.")


class SearchServicesRequestModel(BaseRequestModel):
    filter: ServiceFilterModel | None = Field(default=None)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class ServiceConfigModel(BaseRequestModel):
    model_config = ConfigDict(protected_namespaces=())

    model: str = Field(description="Name or ID of the model VFolder", examples=["ResNet50"])
    model_definition_path: str | None = Field(
        description="Path to the model definition file. If not set, Backend.AI will look for model-definition.yml or model-definition.yaml by default.",
        default=None,
    )
    model_version: int = Field(
        description="Unused; Reserved for future works",
        default=1,
        alias="modelVersion",
    )
    model_mount_destination: str = Field(
        default="/models",
        description=(
            "Mount destination for the model VFolder will be mounted inside the inference"
            " session. Must be set to `/models` when choosing `runtime_variant` other than"
            " `CUSTOM` or `CMD`."
        ),
        alias="modelMountDestination",
    )

    extra_mounts: dict[uuid.UUID, dict[str, Any]] = Field(
        description=(
            "Specifications about extra VFolders mounted to model service session. "
            "MODEL type VFolders are not allowed to be attached to model service session"
            " with this option."
        ),
        default_factory=dict,
    )

    environ: dict[str, str] | None = Field(
        description="Environment variables to be set inside the inference session",
        default=None,
    )
    scaling_group: str = Field(
        description="Name of the resource group to spawn inference sessions",
        examples=["nvidia-H100"],
        alias="scalingGroup",
    )
    resources: dict[str, str | int] | None = Field(
        default=None, examples=[{"cpu": 4, "mem": "32g", "cuda.shares": 2.5}]
    )
    resource_opts: dict[str, str | int | bool] = Field(examples=[{"shmem": "2g"}], default={})


class NewServiceRequestModel(BaseRequestModel):
    model_config = ConfigDict(protected_namespaces=())

    service_name: str = Field(
        description="Name of the service",
        validation_alias=AliasChoices("name", "clientSessionToken"),
        pattern=r"^\w[\w-]*\w$",
        min_length=4,
        max_length=tv.SESSION_NAME_MAX_LENGTH,
    )
    replicas: int = Field(
        description=(
            "Number of sessions to serve traffic. Replacement of"
            " `desired_session_count` (or `desiredSessionCount`)."
        ),
        validation_alias=AliasChoices("desired_session_count", "desiredSessionCount"),
    )
    image: str | None = Field(
        description="String reference of the image which will be used to create session",
        examples=["cr.backend.ai/stable/python-tensorflow:2.7-py38-cuda11.3"],
        alias="lang",
        default=None,
    )
    runtime_variant: RuntimeVariant = Field(
        description="Type of the inference runtime the image will try to load.",
        default=RuntimeVariant.CUSTOM,
    )
    architecture: str | None = Field(
        description=(
            "Changed to nullable in 26.1. Image architecture."
            " If not provided, defaults to the Manager's architecture."
        ),
        alias="arch",
        default=None,
    )
    group_name: str = Field(
        description="Name of project to spawn session",
        default="default",
        validation_alias=AliasChoices("group", "groupName"),
        serialization_alias="group",
    )
    domain_name: str = Field(
        description="Name of domain to spawn session",
        default="default",
        validation_alias=AliasChoices("domain", "domainName"),
        serialization_alias="domain",
    )
    cluster_size: int = Field(
        default=1,
        alias="clusterSize",
    )
    cluster_mode: str = Field(
        default="SINGLE_NODE",
        alias="clusterMode",
    )
    tag: str | None = Field(default=None)
    startup_command: str | None = Field(
        default=None,
        alias="startupCommand",
    )
    bootstrap_script: str | None = Field(
        default=None,
        alias="bootstrapScript",
    )
    callback_url: AnyUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("callbackUrl", "CallbackURL"),
    )
    owner_access_key: str | None = Field(
        description=(
            "(for privileged users only) when specified, transfer ownership of the"
            " inference session to specified user"
        ),
        default=None,
    )
    open_to_public: bool = Field(
        description="If set to true, do not require an API key to access the model service",
        default=False,
    )
    config: ServiceConfigModel


class ScaleRequestModel(BaseRequestModel):
    to: int = Field(description="Ideal number of inference sessions")


class UpdateRouteRequestModel(BaseRequestModel):
    traffic_ratio: NonNegativeFloat


class TokenRequestModel(BaseRequestModel):
    duration: tv.TimeDuration | None = Field(
        default=None, description="The lifetime duration of the token."
    )
    valid_until: int | None = Field(
        default=None,
        description="The absolute token expiry date expressed in the Unix epoch format.",
    )
    expires_at: int = Field(
        default=-1,
        description="The expiration timestamp computed from duration or valid_until.",
    )

    @model_validator(mode="after")
    def check_lifetime(self) -> Self:
        now = datetime.now(UTC)
        if self.valid_until is not None:
            self.expires_at = self.valid_until
        elif self.duration is not None:
            self.expires_at = int((now + self.duration).timestamp())
        else:
            raise ValueError("Either valid_until or duration must be specified.")
        if now.timestamp() > self.expires_at:
            raise ValueError("The expiration time cannot be in the past.")
        return self
