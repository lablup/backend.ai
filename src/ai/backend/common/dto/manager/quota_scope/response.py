from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "GetQuotaScopeResponse",
    "PaginationInfo",
    "QuotaScopeDTO",
    "SearchQuotaScopesResponse",
    "SetQuotaResponse",
    "UnsetQuotaResponse",
)


class QuotaScopeDTO(BaseModel):
    quota_scope_id: str = Field(description="Quota scope ID")
    storage_host_name: str = Field(description="Storage host name")
    usage_bytes: int | None = Field(default=None, description="Current usage in bytes")
    usage_count: int | None = Field(default=None, description="Current usage count")
    hard_limit_bytes: int | None = Field(default=None, description="Hard limit in bytes")


class PaginationInfo(BaseModel):
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class GetQuotaScopeResponse(BaseResponseModel):
    quota_scope: QuotaScopeDTO = Field(description="Quota scope data")


class SearchQuotaScopesResponse(BaseResponseModel):
    quota_scopes: list[QuotaScopeDTO] = Field(description="List of quota scopes")
    pagination: PaginationInfo = Field(description="Pagination information")


class SetQuotaResponse(BaseResponseModel):
    quota_scope: QuotaScopeDTO = Field(description="Updated quota scope")


class UnsetQuotaResponse(BaseResponseModel):
    quota_scope: QuotaScopeDTO = Field(description="Quota scope after unsetting quota")
