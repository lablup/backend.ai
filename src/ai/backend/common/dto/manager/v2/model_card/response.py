from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardAccessLevel
from ai.backend.common.identifier.vfolder import VFolderUUID


class ResourceSlotEntryInfo(BaseResponseModel):
    resource_type: str = Field(description="Resource type name.")
    quantity: str = Field(description="Resource quantity.")


class ModelCardMetadata(BaseResponseModel):
    author: str | None = Field(default=None)
    title: str | None = Field(default=None)
    model_version: str | None = Field(default=None)
    description: str | None = Field(default=None)
    task: str | None = Field(default=None)
    category: str | None = Field(default=None)
    architecture: str | None = Field(default=None)
    framework: list[str] = Field(default_factory=list)
    label: list[str] = Field(default_factory=list)
    license: str | None = Field(default=None)


class ModelCardNode(BaseResponseModel):
    id: UUID = Field(description="Model card ID.")
    name: str = Field(description="Model card name.")
    vfolder_id: VFolderUUID = Field(description="VFolder ID.")
    domain_name: str = Field(description="Domain name.")
    project_id: UUID = Field(description="Project ID.")
    creator_id: UUID = Field(description="Creator user ID.")
    metadata: ModelCardMetadata = Field(description="Model metadata.")
    min_resource: list[ResourceSlotEntryInfo] | None = Field(default=None)
    readme: str | None = Field(default=None)
    access_level: ModelCardAccessLevel = Field(description="Access level of the model card.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None)


class CreateModelCardPayload(BaseResponseModel):
    model_card: ModelCardNode = Field(description="The created model card.")


class UpdateModelCardPayload(BaseResponseModel):
    model_card: ModelCardNode = Field(description="The updated model card.")


class DeleteModelCardPayload(BaseResponseModel):
    id: UUID = Field(description="ID of the deleted model card.")


class SearchModelCardsPayload(BaseResponseModel):
    items: list[ModelCardNode] = Field(description="List of model cards.")
    total_count: int = Field(description="Total number of matching items.")
    has_next_page: bool = Field(description="Whether there are more items after.")
    has_previous_page: bool = Field(description="Whether there are more items before.")


class BulkDeleteModelCardV2Error(BaseResponseModel):
    """Error information for a single model card that failed during bulk deletion."""

    card_id: UUID = Field(description="UUID of the model card that failed to delete.")
    message: str = Field(description="Error message describing the failure.")


class BulkDeleteModelCardsPayload(BaseResponseModel):
    """Payload for bulk model card deletion mutation."""

    successes: list[UUID] = Field(
        description="UUIDs of model cards that were successfully deleted.",
    )
    failed: list[BulkDeleteModelCardV2Error] = Field(
        description="List of errors for model cards that failed to delete.",
    )


class ScanProjectModelCardsPayload(BaseResponseModel):
    created_count: int = Field(description="Number of newly created model cards.")
    updated_count: int = Field(description="Number of updated existing model cards.")
    errors: list[str] = Field(default_factory=list, description="Per-vfolder error messages.")


class DeployModelCardPayload(BaseResponseModel):
    deployment_id: UUID = Field(description="ID of the created deployment.")
    deployment_name: str = Field(description="Name of the created deployment.")
