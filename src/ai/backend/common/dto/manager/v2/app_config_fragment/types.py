"""
Common types for app_config_fragment DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "AppConfigFragmentOrderField",
    "AppConfigScopeType",
    "OrderDirection",
)


class AppConfigFragmentOrderField(StrEnum):
    """Fields available for ordering app-config fragments."""

    SCOPE_TYPE = "scope_type"
    SCOPE_ID = "scope_id"
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
