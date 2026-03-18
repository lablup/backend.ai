from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    OrderDirection,
    QuotaScopeOrderField,
)

__all__ = (
    "GetQuotaScopeRequest",
    "QuotaScopeFilter",
    "QuotaScopeOrder",
    "SearchQuotaScopesRequest",
    "SetQuotaRequest",
    "UnsetQuotaRequest",
)


class QuotaScopeFilter(BaseRequestModel):
    quota_scope_id: StringFilter | None = Field(
        default=None, description="Filter by quota scope ID"
    )
    storage_host_name: StringFilter | None = Field(
        default=None, description="Filter by storage host name"
    )


class QuotaScopeOrder(BaseRequestModel):
    field: QuotaScopeOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class GetQuotaScopeRequest(BaseRequestModel):
    pass


class SearchQuotaScopesRequest(BaseRequestModel):
    filter: QuotaScopeFilter | None = Field(default=None, description="Filter conditions")
    order: list[QuotaScopeOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SetQuotaRequest(BaseRequestModel):
    storage_host_name: str = Field(description="Storage host name")
    quota_scope_id: str = Field(
        description="Quota scope ID (e.g. 'user:<uuid>' or 'project:<uuid>')"
    )
    hard_limit_bytes: int = Field(description="Hard limit in bytes for the quota scope")


class UnsetQuotaRequest(BaseRequestModel):
    storage_host_name: str = Field(description="Storage host name")
    quota_scope_id: str = Field(
        description="Quota scope ID (e.g. 'user:<uuid>' or 'project:<uuid>')"
    )
