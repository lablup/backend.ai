"""
Response DTOs for quota_scope DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

__all__ = (
    "GetQuotaScopePayload",
    "QuotaScopeNode",
    "SearchQuotaScopesPayload",
    "SetQuotaPayload",
    "UnsetQuotaPayload",
)


class QuotaScopeNode(BaseResponseModel):
    """Node model representing a quota scope entity."""

    quota_scope_id: str = Field(
        description="Quota scope ID (e.g. 'user:<uuid>' or 'project:<uuid>')"
    )
    storage_host_name: str = Field(description="Storage host name")
    usage_bytes: int | None = Field(default=None, description="Current usage in bytes")
    usage_count: int | None = Field(default=None, description="Current usage count")
    hard_limit_bytes: int | None = Field(default=None, description="Hard limit in bytes")


class SearchQuotaScopesPayload(BaseResponseModel):
    """Payload for quota scope search query result."""

    quota_scopes: list[QuotaScopeNode] = Field(description="List of quota scopes")
    pagination: PaginationInfo = Field(description="Pagination information")


class GetQuotaScopePayload(BaseResponseModel):
    """Payload for single quota scope retrieval result."""

    quota_scope: QuotaScopeNode = Field(description="Quota scope data")


class SetQuotaPayload(BaseResponseModel):
    """Payload for set quota mutation result."""

    quota_scope: QuotaScopeNode = Field(description="Updated quota scope")


class UnsetQuotaPayload(BaseResponseModel):
    """Payload for unset quota mutation result."""

    quota_scope: QuotaScopeNode = Field(description="Quota scope after unsetting quota")
