"""Types for app-config-policy repository operations."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData


@dataclass
class AppConfigPolicySearchResult:
    """Result from searching app-config policies."""

    items: list[AppConfigPolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
