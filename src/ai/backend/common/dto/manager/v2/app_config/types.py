"""
Common types for AppConfig (merged view) DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "AppConfigOrderField",
    "AppConfigScopeType",
    "OrderDirection",
)


class AppConfigOrderField(StrEnum):
    """Fields available for ordering AppConfig merged-view results."""

    USER_ID = "user_id"
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
