from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.deployment.types import (
    ModelMetadataInfoDTO,
    PreStartActionInfoDTO,
)


class RuntimeVariantModelHealthCheckInfo(BaseResponseModel):
    enable: bool | None = Field(default=None, description="Whether health checks are enabled.")
    interval: float | None = Field(default=None, description="Health-check interval in seconds.")
    path: str | None = Field(default=None, description="Health-check endpoint path.")
    max_retries: int | None = Field(default=None, description="Maximum number of retries.")
    max_wait_time: float | None = Field(
        default=None, description="Maximum time to wait for a health check."
    )
    expected_status_code: int | None = Field(
        default=None, description="Expected healthy HTTP status code."
    )
    initial_delay: float | None = Field(
        default=None, description="Initial health-check grace period in seconds."
    )


class RuntimeVariantModelServiceConfigInfo(BaseResponseModel):
    pre_start_actions: list[PreStartActionInfoDTO] | None = Field(
        default=None, description="Actions to run before starting the model service."
    )
    command: str | None = Field(
        default=None,
        validation_alias=AliasChoices("command", "start_command"),
        description="Command that starts the model service.",
    )
    shell: str | None = Field(default=None, description="Shell used to run the command.")
    port: int | None = Field(default=None, description="Model service port.")
    health_check: RuntimeVariantModelHealthCheckInfo | None = Field(
        default=None, description="Default model service health-check settings."
    )


class RuntimeVariantModelConfigInfo(BaseResponseModel):
    name: str | None = Field(default=None, description="Default model name.")
    model_path: str | None = Field(default=None, description="Default model path.")
    service: RuntimeVariantModelServiceConfigInfo | None = Field(
        default=None, description="Default model service configuration."
    )
    metadata: ModelMetadataInfoDTO | None = Field(
        default=None, description="Default model metadata."
    )


class RuntimeVariantModelDefinitionInfo(BaseResponseModel):
    models: list[RuntimeVariantModelConfigInfo] | None = Field(
        default=None, description="Default model configurations supplied by the runtime variant."
    )


class RuntimeVariantNode(BaseResponseModel):
    id: UUID = Field(description="ID of the runtime variant.")
    name: str = Field(description="Unique name of the runtime variant.")
    description: str | None = Field(default=None, description="Description.")
    reads_vfolder_config_files: bool = Field(
        description=(
            "Whether legacy model configuration files in the model vfolder participate in "
            "revision resolution."
        )
    )
    default_model_definition: RuntimeVariantModelDefinitionInfo = Field(
        description="Model definition defaults stored for the runtime variant."
    )
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class CreateRuntimeVariantPayload(BaseResponseModel):
    runtime_variant: RuntimeVariantNode = Field(description="The created runtime variant.")


class UpdateRuntimeVariantPayload(BaseResponseModel):
    runtime_variant: RuntimeVariantNode = Field(description="The updated runtime variant.")


class DeleteRuntimeVariantPayload(BaseResponseModel):
    id: UUID = Field(description="ID of the deleted runtime variant.")


class DeleteRuntimeVariantsPayload(BaseResponseModel):
    """Payload for bulk runtime variant deletion."""

    deleted_count: int = Field(description="Number of runtime variants successfully deleted.")


class SearchRuntimeVariantsPayload(BaseResponseModel):
    items: list[RuntimeVariantNode] = Field(description="List of runtime variants.")
    total_count: int = Field(description="Total number of matching items.")
    has_next_page: bool = Field(description="Whether there are more items after.")
    has_previous_page: bool = Field(description="Whether there are more items before.")
