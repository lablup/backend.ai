"""
Request DTOs for quota_scope DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter

from .types import OrderDirection, QuotaScopeOrderField

__all__ = (
    "QuotaScopeFilter",
    "QuotaScopeOrder",
    "SearchQuotaScopesInput",
    "SetQuotaInput",
    "UnsetQuotaInput",
)


class QuotaScopeFilter(BaseRequestModel):
    """Filter conditions for quota scope queries."""

    quota_scope_id: StringFilter | None = Field(
        default=None, description="Filter by quota scope ID"
    )
    storage_host_name: StringFilter | None = Field(
        default=None, description="Filter by storage host name"
    )


class QuotaScopeOrder(BaseRequestModel):
    """Order specification for quota scope queries."""

    field: QuotaScopeOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchQuotaScopesInput(BaseRequestModel):
    """Input for searching quota scopes with optional filtering, ordering, and pagination."""

    filter: QuotaScopeFilter | None = Field(default=None, description="Filter conditions")
    order: list[QuotaScopeOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Maximum items to return",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SetQuotaInput(BaseRequestModel):
    """Input for setting a quota on a quota scope."""

    storage_host_name: str = Field(description="Storage host name")
    quota_scope_id: str = Field(
        description="Quota scope ID (e.g. 'user:<uuid>' or 'project:<uuid>')"
    )
    hard_limit_bytes: int = Field(ge=0, description="Hard limit in bytes for the quota scope")


class UnsetQuotaInput(BaseRequestModel):
    """Input for unsetting (removing) a quota from a quota scope."""

    storage_host_name: str = Field(description="Storage host name")
    quota_scope_id: str = Field(
        description="Quota scope ID (e.g. 'user:<uuid>' or 'project:<uuid>')"
    )
