"""
Common types for keypair DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "KeypairOrderField",
    "OrderDirection",
)


class KeypairOrderField(StrEnum):
    """Keypair ordering field."""

    CREATED_AT = "created_at"
    LAST_USED = "last_used"
    ACCESS_KEY = "access_key"
    IS_ACTIVE = "is_active"
    RESOURCE_POLICY = "resource_policy"
