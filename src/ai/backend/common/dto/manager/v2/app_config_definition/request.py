"""Request DTOs for app_config_definition v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
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


class SearchAppConfigDefinitionsInput(BaseRequestModel):
    """Input for paginated app config definition search."""

    limit: int | None = Field(
        default=None, ge=1, description="Offset-based: maximum number of results."
    )
    offset: int | None = Field(
        default=None, ge=0, description="Offset-based: number of results to skip."
    )
