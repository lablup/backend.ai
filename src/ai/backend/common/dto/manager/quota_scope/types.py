from __future__ import annotations

from enum import StrEnum

__all__ = (
    "QuotaScopeOrderField",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class QuotaScopeOrderField(StrEnum):
    QUOTA_SCOPE_ID = "quota_scope_id"
    STORAGE_HOST_NAME = "storage_host_name"
