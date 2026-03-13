from __future__ import annotations

import uuid

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel


class ListPresetsQuery(BaseRequestModel):
    """Query parameters for listing resource presets."""

    scaling_group: str | None = Field(default=None, description="Scaling group name to filter by")


class CheckPresetsRequest(BaseRequestModel):
    """Request body for checking resource presets allocatability."""

    scaling_group: str | None = Field(default=None, description="Scaling group name")
    group: str = Field(description="User group name")


class UsagePerMonthRequest(BaseRequestModel):
    """Request body for querying monthly usage statistics."""

    group_ids: list[uuid.UUID] | None = Field(description="Group IDs to query")
    month: str = Field(description="Year-month in YYYYMM format")


class UsagePerPeriodRequest(BaseRequestModel):
    """Request body for querying usage statistics over a date range."""

    project_id: uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("project_id", "group_id"),
        description="Project (group) ID to filter",
    )
    start_date: str = Field(description="Start date in YYYYMMDD format")
    end_date: str = Field(description="End date in YYYYMMDD format")


class WatcherAgentRequest(BaseRequestModel):
    """Request body for watcher agent operations."""

    agent_id: str = Field(
        validation_alias=AliasChoices("agent_id", "agent"),
        description="Agent ID",
    )


class UsagePerMonthQuery(BaseRequestModel):
    """Query parameters for monthly usage statistics (GET)."""

    group_ids: list[uuid.UUID] | None = Field(default=None, description="Group IDs to query")
    month: str = Field(description="Year-month in YYYYMM format")


class UsagePerPeriodQuery(BaseRequestModel):
    """Query parameters for usage statistics over a date range (GET)."""

    project_id: uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("project_id", "group_id"),
        description="Project (group) ID to filter",
    )
    start_date: str = Field(description="Start date in YYYYMMDD format")
    end_date: str = Field(description="End date in YYYYMMDD format")


class WatcherStatusQuery(BaseRequestModel):
    """Query parameters for watcher status (GET)."""

    agent_id: str = Field(
        validation_alias=AliasChoices("agent_id", "agent"),
        description="Agent ID",
    )
