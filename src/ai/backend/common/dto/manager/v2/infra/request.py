"""
Request DTOs for infra DTO v2.
"""

from __future__ import annotations

import uuid

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "CheckPresetsInput",
    "GetWSProxyVersionInput",
    "ListPresetsInput",
    "ListScalingGroupsInput",
    "UsagePerMonthInput",
    "UsagePerPeriodInput",
    "WatcherAgentInput",
)


class ListScalingGroupsInput(BaseRequestModel):
    """Input for listing available scaling groups for a given user group."""

    group: str | uuid.UUID = Field(
        ...,
        validation_alias=AliasChoices("group", "group_id", "group_name"),
        description="Group identifier (name or UUID) to list scaling groups for.",
    )


class GetWSProxyVersionInput(BaseRequestModel):
    """Input for getting the wsproxy version of a scaling group."""

    group: str | uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("group", "group_id", "group_name"),
        description="Group identifier (name or UUID) for access control filtering.",
    )


class ListPresetsInput(BaseRequestModel):
    """Input for listing resource presets."""

    scaling_group: str | None = Field(
        default=None,
        description="Scaling group name to filter presets by.",
    )


class CheckPresetsInput(BaseRequestModel):
    """Input for checking resource presets with allocatability information."""

    scaling_group: str | None = Field(
        default=None,
        description="Scaling group name to check presets for.",
    )
    group: str = Field(description="User group name to check resource limits against.")


class UsagePerMonthInput(BaseRequestModel):
    """Input for querying container usage statistics for a specified month."""

    group_ids: list[str] | None = Field(
        default=None,
        description="List of group IDs to filter usage by. Null to include all groups.",
    )
    month: str = Field(
        description="Year-month in YYYYMM format (e.g., '202006' for June 2020).",
        pattern=r"^\d{6}$",
    )


class UsagePerPeriodInput(BaseRequestModel):
    """Input for querying container usage statistics for a specified date range."""

    project_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("project_id", "group_id"),
        description="Project (group) ID to filter usage by.",
    )
    start_date: str = Field(
        description="Start date in YYYYMMDD format.",
        pattern=r"^\d{8}$",
    )
    end_date: str = Field(
        description="End date in YYYYMMDD format.",
        pattern=r"^\d{8}$",
    )


class WatcherAgentInput(BaseRequestModel):
    """Input for watcher operations (status, start, stop, restart) on an agent."""

    agent_id: str = Field(
        ...,
        validation_alias=AliasChoices("agent_id", "agent"),
        description="The agent ID to perform watcher operations on.",
    )
