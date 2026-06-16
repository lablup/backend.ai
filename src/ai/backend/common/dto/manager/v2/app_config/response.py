"""
Response DTOs for AppConfig (merged view) DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentBulkError,
    AppConfigFragmentNode,
)

__all__ = (
    "AppConfigNode",
    "MyBulkCreateAppConfigFragmentsPayload",
    "MyBulkUpdateAppConfigFragmentsPayload",
    "GetUserAppConfigPayload",
    "SearchAppConfigsPayload",
)


class AppConfigNode(BaseResponseModel):
    """Merged per-user AppConfig view.

    `fragments` are ordered low → high merge priority (by fragment
    `rank`). `config` is the deep-merged result, projected to `None`
    when every contributing fragment is empty (§3 null projection).
    """

    user_id: UUID = Field(description="Target user's UUID.")
    name: str = Field(description="Policy / config name.")
    fragments: list[AppConfigFragmentNode] = Field(
        description="Contributing fragments in merge order (low → high).",
    )
    config: dict[str, Any] | None = Field(
        default=None,
        description="Deep-merged configuration, or null when every fragment is empty.",
    )


class GetUserAppConfigPayload(BaseResponseModel):
    """Payload for reading a single merged AppConfig."""

    item: AppConfigNode | None = Field(
        default=None,
        description="Merged AppConfig, or null when no fragments exist for the user.",
    )


class SearchAppConfigsPayload(BaseResponseModel):
    """Payload for paginated merged-view AppConfig search."""

    items: list[AppConfigNode] = Field(description="AppConfigs matching the filter.")
    total_count: int = Field(description="Total number of AppConfigs matching the filter.")
    has_next_page: bool = Field(default=False, description="Whether there is a next page.")
    has_previous_page: bool = Field(default=False, description="Whether there is a previous page.")


class MyBulkCreateAppConfigFragmentsPayload(BaseResponseModel):
    """Payload for `myBulkCreateAppConfigFragments`.

    Each successfully created row produces a recomputed merged
    `AppConfigNode`; failures are collected per-item.
    """

    created: list[AppConfigNode] = Field(
        description="Recomputed merged AppConfig views for each created USER fragment.",
    )
    failed: list[AppConfigFragmentBulkError] = Field(description="Per-item failures.")


class MyBulkUpdateAppConfigFragmentsPayload(BaseResponseModel):
    """Payload for `myBulkUpdateAppConfigFragments`."""

    updated: list[AppConfigNode] = Field(
        description="Recomputed merged AppConfig views for each updated USER fragment.",
    )
    failed: list[AppConfigFragmentBulkError] = Field(description="Per-item failures.")
