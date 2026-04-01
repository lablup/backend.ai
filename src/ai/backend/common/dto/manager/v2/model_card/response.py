from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel


class ResourceSlotEntryInfo(BaseResponseModel):
    resource_type: str = Field(description="Resource type name.")
    quantity: str = Field(description="Resource quantity.")


class ModelCardNode(BaseResponseModel):
    id: UUID = Field(description="Model card ID.")
    name: str = Field(description="Model card name.")
    vfolder_id: UUID = Field(description="VFolder ID.")
    domain_name: str = Field(description="Domain name.")
    project_id: UUID = Field(description="Project ID.")
    creator_id: UUID = Field(description="Creator user ID.")
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
    min_resource: list[ResourceSlotEntryInfo] | None = Field(default=None)
    readme: str | None = Field(default=None)
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
