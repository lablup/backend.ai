"""
Common types for keypair system.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "KeyPairOrderField",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class KeyPairOrderField(StrEnum):
    """Fields available for ordering keypairs."""

    ACCESS_KEY = "access_key"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    LAST_USED = "last_used"
    RATE_LIMIT = "rate_limit"
    NUM_QUERIES = "num_queries"
