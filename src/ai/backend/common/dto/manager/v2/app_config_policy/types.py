"""
Common types for app_config_policy DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "AppConfigPolicyOrderField",
)


class AppConfigPolicyOrderField(StrEnum):
    """Fields available for ordering app config policies."""

    CONFIG_NAME = "config_name"
    CREATED_AT = "created_at"
