from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.deployment.types import (
    ModelHealthCheckInfoDTO,
    ModelMetadataInfoDTO,
    PreStartActionInfoDTO,
)


class DeploymentRevisionPresetOrderField(StrEnum):
    NAME = "name"
    RANK = "rank"
    CREATED_AT = "created_at"


class PresetModelServiceConfigInfoDTO(BaseResponseModel):
    """Output DTO for a preset-stored model service configuration."""

    pre_start_actions: list[PreStartActionInfoDTO] = Field(
        default_factory=list,
        description="List of pre-start actions to execute before starting the model service.",
    )
    command: str | None = Field(
        default=None,
        description="Single-string command to start the model service.",
    )
    start_command: list[str] | None = Field(
        default=None,
        description=(
            "Deprecated. Command to start the model service. Do not set together with "
            "`command`; when both are set, `command` takes precedence and this field is ignored."
        ),
    )
    shell: str | None = Field(
        default="/bin/bash",
        description=(
            "Shell used to run the command. If set, the kernel runs "
            "`[shell, '-c', command]`; null or empty disables shell wrapping."
        ),
    )
    port: int | None = Field(
        default=None,
        description="Port number for the model service. Null when the preset omits it to "
        "inherit the runtime variant baseline's port at revision resolution.",
    )
    health_check: ModelHealthCheckInfoDTO | None = Field(
        default=None, description="Health check configuration for the model service."
    )


class PresetModelConfigInfoDTO(BaseResponseModel):
    """Output DTO for a single model entry in a preset model definition."""

    name: str | None = Field(
        default=None,
        description="Name of the model. Null when the preset omits it to inherit the "
        "runtime variant baseline's name at revision resolution.",
    )
    model_path: str | None = Field(
        default=None,
        description="Path to the model file. Null when the preset omits it to inherit the "
        "model mount destination at revision resolution.",
    )
    service: PresetModelServiceConfigInfoDTO | None = Field(
        default=None, description="Configuration for the model service."
    )
    metadata: ModelMetadataInfoDTO | None = Field(
        default=None, description="Metadata about the model."
    )


class PresetModelDefinitionInfoDTO(BaseResponseModel):
    """Output DTO for a preset-stored model definition."""

    models: list[PresetModelConfigInfoDTO] = Field(
        description="List of models in the model definition."
    )
