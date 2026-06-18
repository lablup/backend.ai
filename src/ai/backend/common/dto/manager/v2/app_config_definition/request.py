"""Request DTOs for app_config_definition v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.app_config_definition.types import (
    AppConfigDefinitionOrderField,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "AppConfigDefinitionFilter",
    "AppConfigDefinitionOrder",
    "CreateAppConfigDefinitionInput",
    "SearchAppConfigDefinitionsInput",
)


class CreateAppConfigDefinitionInput(BaseRequestModel):
    """Input for registering a new app config definition."""

    config_name: str = Field(
        min_length=1,
        max_length=128,
        description="Unique config name to register (e.g. 'theme', 'menu').",
    )


class AppConfigDefinitionFilter(BaseRequestModel):
    """Filter for app config definition search."""

    config_name: StringFilter | None = Field(default=None, description="Filter by config name.")
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter by creation datetime."
    )
    updated_at: DateTimeFilter | None = Field(
        default=None, description="Filter by last update datetime."
    )


class AppConfigDefinitionOrder(BaseRequestModel):
    """Order specifier for app config definition search."""

    field: AppConfigDefinitionOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchAppConfigDefinitionsInput(BaseRequestModel):
    """Input for paginated app config definition search."""

    filter: AppConfigDefinitionFilter | None = Field(default=None, description="Filter conditions.")
    order: list[AppConfigDefinitionOrder] | None = Field(
        default=None, description="Order specifiers, applied in sequence."
    )
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size.")
    after: str | None = Field(default=None, description="Cursor-forward start cursor.")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size.")
    before: str | None = Field(default=None, description="Cursor-backward end cursor.")
    limit: int | None = Field(
        default=None, ge=1, description="Offset-based: maximum number of results."
    )
    offset: int | None = Field(
        default=None, ge=0, description="Offset-based: number of results to skip."
    )
