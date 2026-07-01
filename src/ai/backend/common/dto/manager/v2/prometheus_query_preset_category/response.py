"""
Response DTOs for prometheus_query_preset_category DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "CategoryNode",
    "CreateCategoryPayload",
    "DeleteCategoryPayload",
    "GetCategoryPayload",
    "SearchCategoriesPayload",
    "CreateCategoryGQLPayload",
)


class CategoryNode(BaseResponseModel):
    """Node representing a single prometheus query preset category."""

    id: UUID = Field(description="Category ID")
    name: str = Field(description="Human-readable category name")
    description: str | None = Field(default=None, description="Optional category description")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class CreateCategoryPayload(BaseResponseModel):
    """Payload for creating a category."""

    item: CategoryNode = Field(description="Created category")


class DeleteCategoryPayload(BaseResponseModel):
    """Payload for deleting a category."""

    id: UUID = Field(description="Deleted category ID")


class GetCategoryPayload(BaseResponseModel):
    """Payload for getting a single category."""

    item: CategoryNode | None = Field(default=None, description="Category data")


class CreateCategoryGQLPayload(BaseResponseModel):
    """GQL-layer payload returned after creating a category."""

    category: CategoryNode = Field(description="Created category.")


class SearchCategoriesPayload(BaseResponseModel):
    """Payload for paginated category search results."""

    items: list[CategoryNode] = Field(description="List of category nodes.")
    total_count: int = Field(description="Total number of categories matching the filter.")
    has_next_page: bool = Field(default=False, description="Whether there is a next page.")
    has_previous_page: bool = Field(default=False, description="Whether there is a previous page.")
