from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel


class RuntimeVariantNode(BaseResponseModel):
    id: UUID = Field(description="ID of the runtime variant.")
    name: str = Field(description="Unique name of the runtime variant.")
    description: str | None = Field(default=None, description="Description.")
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
