from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.quota_scope import (
    SearchQuotaScopesRequest,
    SearchQuotaScopesResponse,
    SetQuotaRequest,
    SetQuotaResponse,
    UnsetQuotaRequest,
    UnsetQuotaResponse,
)
from ai.backend.common.dto.manager.quota_scope.response import (
    GetQuotaScopeResponse,
)

_BASE_PATH = "/admin/quota-scopes"


class QuotaScopeClient(BaseDomainClient):
    """Client for quota scope management endpoints."""

    async def get(
        self,
        storage_host_name: str,
        quota_scope_id: str,
    ) -> GetQuotaScopeResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{storage_host_name}/{quota_scope_id}",
            response_model=GetQuotaScopeResponse,
        )

    async def search(
        self,
        request: SearchQuotaScopesRequest,
    ) -> SearchQuotaScopesResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/search",
            request=request,
            response_model=SearchQuotaScopesResponse,
        )

    async def set_quota(
        self,
        request: SetQuotaRequest,
    ) -> SetQuotaResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/set",
            request=request,
            response_model=SetQuotaResponse,
        )

    async def unset_quota(
        self,
        request: UnsetQuotaRequest,
    ) -> UnsetQuotaResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/unset",
            request=request,
            response_model=UnsetQuotaResponse,
        )
