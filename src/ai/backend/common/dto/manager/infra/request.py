"""
Request DTOs for Infrastructure REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    # etcd requests
    "GetResourceMetadataRequest",
    "GetConfigRequest",
    "SetConfigRequest",
    "DeleteConfigRequest",
    # scaling_group requests
    "ListScalingGroupsRequest",
    "GetWSProxyVersionRequest",
    # resource requests
    "ListPresetsRequest",
    "CheckPresetsRequest",
    "UsagePerMonthRequest",
    "UsagePerPeriodRequest",
    "WatcherAgentRequest",
)


# --- etcd.py requests ---


class GetResourceMetadataRequest(BaseRequestModel):
    """Request for fetching resource slot metadata, optionally filtered by scaling group."""

    sgroup: str | None = Field(
        default=None,
        description="Scaling group name to filter available resource slots by.",
    )


class GetConfigRequest(BaseRequestModel):
    """Request for reading etcd configuration key-value pairs."""

    key: str = Field(description="The etcd key to read.")
    prefix: bool = Field(
        default=False,
        description="If true, read all keys matching the given prefix.",
    )


class SetConfigRequest(BaseRequestModel):
    """Request for writing etcd configuration key-value pairs."""

    key: str = Field(description="The etcd key to write.")
    value: Any = Field(description="The value to set. Can be a scalar or a nested mapping.")


class DeleteConfigRequest(BaseRequestModel):
    """Request for deleting etcd configuration key-value pairs."""

    key: str = Field(description="The etcd key to delete.")
    prefix: bool = Field(
        default=False,
        description="If true, delete all keys matching the given prefix.",
    )


# --- scaling_group.py requests ---


class ListScalingGroupsRequest(BaseRequestModel):
    """Request for listing available scaling groups for a given user group."""

    group: str | uuid.UUID = Field(
        ...,
        validation_alias=AliasChoices("group", "group_id", "group_name"),
        description="Group identifier (name or UUID) to list scaling groups for.",
    )


class GetWSProxyVersionRequest(BaseRequestModel):
    """Request for getting the wsproxy version of a scaling group."""

    group: str | uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("group", "group_id", "group_name"),
        description="Group identifier (name or UUID) for access control filtering.",
    )


# --- resource.py requests ---


class ListPresetsRequest(BaseRequestModel):
    """Request for listing resource presets."""

    scaling_group: str | None = Field(
        default=None,
        description="Scaling group name to filter presets by.",
    )


class CheckPresetsRequest(BaseRequestModel):
    """Request for checking resource presets with allocatability information."""

    scaling_group: str | None = Field(
        default=None,
        description="Scaling group name to check presets for.",
    )
    group: str = Field(description="User group name to check resource limits against.")


class UsagePerMonthRequest(BaseRequestModel):
    """Request for querying container usage statistics for a specified month."""

    group_ids: list[str] | None = Field(
        default=None,
        description="List of group IDs to filter usage by. If null, includes all groups.",
    )
    month: str = Field(
        description="Year-month in YYYYMM format (e.g., '202006' for June 2020).",
        pattern=r"^\d{6}",
    )


class UsagePerPeriodRequest(BaseRequestModel):
    """Request for querying container usage statistics for a specified date range."""

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


class WatcherAgentRequest(BaseRequestModel):
    """Request for watcher operations (status, start, stop, restart) on an agent."""

    agent_id: str = Field(
        ...,
        validation_alias=AliasChoices("agent_id", "agent"),
        description="The agent ID to perform watcher operations on.",
    )
