"""
Common types for quota_scope DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "QuotaScopeOrderField",
)


class QuotaScopeOrderField(StrEnum):
    """Fields available for ordering quota scopes."""

    QUOTA_SCOPE_ID = "quota_scope_id"
    STORAGE_HOST_NAME = "storage_host_name"
