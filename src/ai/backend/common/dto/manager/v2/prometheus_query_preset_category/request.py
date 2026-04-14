"""
Request DTOs for prometheus_query_preset_category DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import CategoryOrderField, OrderDirection

__all__ = (
    "CreateCategoryInput",
    "DeleteCategoryInput",
    "CategoryFilter",
    "CategoryOrder",
    "SearchCategoriesInput",
)

_DEFAULT_PAGE_LIMIT = 50


class CreateCategoryInput(BaseRequestModel):
    """Input for creating a prometheus query preset category."""

    name: str = Field(min_length=1, max_length=128, description="Human-readable category name")
    description: str | None = Field(default=None, description="Optional category description")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class DeleteCategoryInput(BaseRequestModel):
    """Input for deleting a prometheus query preset category."""

    id: UUID = Field(description="Category ID to delete")


class CategoryFilter(BaseRequestModel):
    """Filter for prometheus query preset category search."""

    name: StringFilter | None = Field(default=None, description="Filter by name")


class CategoryOrder(BaseRequestModel):
    """Order specification for prometheus query preset categories."""

    field: CategoryOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchCategoriesInput(BaseRequestModel):
    """Input for searching prometheus query preset categories with filters, orders, and pagination."""

    filter: CategoryFilter | None = Field(default=None, description="Filter conditions")
    order: list[CategoryOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(
        default=_DEFAULT_PAGE_LIMIT, ge=1, le=1000, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
