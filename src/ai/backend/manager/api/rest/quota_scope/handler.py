"""Quota scope handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.quota_scope import (
    GetQuotaScopeResponse,
    PaginationInfo,
    QuotaScopeDTO,
    SearchQuotaScopesRequest,
    SearchQuotaScopesResponse,
    SetQuotaRequest,
    SetQuotaResponse,
    UnsetQuotaRequest,
    UnsetQuotaResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.quota_scope_request import GetQuotaScopePathParam
from ai.backend.manager.services.vfs_storage.actions.get_quota_scope import GetQuotaScopeAction
from ai.backend.manager.services.vfs_storage.actions.search_quota_scopes import (
    SearchQuotaScopesAction,
)
from ai.backend.manager.services.vfs_storage.actions.set_quota_scope import SetQuotaScopeAction
from ai.backend.manager.services.vfs_storage.actions.unset_quota_scope import UnsetQuotaScopeAction

if TYPE_CHECKING:
    from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class QuotaScopeHandler:
    """Quota scope API handler with constructor-injected dependencies."""

    def __init__(self, *, vfs_storage: VFSStorageProcessors) -> None:
        self._vfs_storage = vfs_storage

    async def get(
        self,
        path: PathParam[GetQuotaScopePathParam],
        ctx: UserContext,
    ) -> APIResponse:
        """Get a single quota scope by storage host and scope ID."""
        log.info("GET (ak:{})", ctx.access_key)
        result = await self._vfs_storage.get_quota_scope.wait_for_complete(
            GetQuotaScopeAction(
                storage_host_name=path.parsed.storage_host_name,
                quota_scope_id=path.parsed.quota_scope_id,
            )
        )
        dto = QuotaScopeDTO(
            quota_scope_id=result.quota_scope_id,
            storage_host_name=result.storage_host_name,
            usage_bytes=result.usage_bytes,
            usage_count=result.usage_count,
            hard_limit_bytes=result.hard_limit_bytes,
        )
        resp = GetQuotaScopeResponse(quota_scope=dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search(
        self,
        body: BodyParam[SearchQuotaScopesRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search all quota scopes across all volumes."""
        log.info("SEARCH (ak:{})", ctx.access_key)
        result = await self._vfs_storage.search_quota_scopes.wait_for_complete(
            SearchQuotaScopesAction()
        )
        quota_scopes = [
            QuotaScopeDTO(
                quota_scope_id=qs.quota_scope_id,
                storage_host_name=qs.storage_host_name,
                usage_bytes=qs.usage_bytes,
                usage_count=qs.usage_count,
                hard_limit_bytes=qs.hard_limit_bytes,
            )
            for qs in result.quota_scopes
        ]
        total_count = len(quota_scopes)
        offset = body.parsed.offset
        limit = body.parsed.limit
        paginated = quota_scopes[offset : offset + limit]
        resp = SearchQuotaScopesResponse(
            quota_scopes=paginated,
            pagination=PaginationInfo(
                total=total_count,
                offset=offset,
                limit=limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def set_quota(
        self,
        body: BodyParam[SetQuotaRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Set quota limit for a scope."""
        log.info("SET_QUOTA (ak:{})", ctx.access_key)
        result = await self._vfs_storage.set_quota_scope.wait_for_complete(
            SetQuotaScopeAction(
                storage_host_name=body.parsed.storage_host_name,
                quota_scope_id=body.parsed.quota_scope_id,
                hard_limit_bytes=body.parsed.hard_limit_bytes,
            )
        )
        dto = QuotaScopeDTO(
            quota_scope_id=result.quota_scope_id,
            storage_host_name=result.storage_host_name,
            usage_bytes=result.usage_bytes,
            usage_count=result.usage_count,
            hard_limit_bytes=result.hard_limit_bytes,
        )
        resp = SetQuotaResponse(quota_scope=dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def unset_quota(
        self,
        body: BodyParam[UnsetQuotaRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Unset (remove) quota limit for a scope."""
        log.info("UNSET_QUOTA (ak:{})", ctx.access_key)
        result = await self._vfs_storage.unset_quota_scope.wait_for_complete(
            UnsetQuotaScopeAction(
                storage_host_name=body.parsed.storage_host_name,
                quota_scope_id=body.parsed.quota_scope_id,
            )
        )
        dto = QuotaScopeDTO(
            quota_scope_id=result.quota_scope_id,
            storage_host_name=result.storage_host_name,
            usage_bytes=None,
            usage_count=None,
            hard_limit_bytes=None,
        )
        resp = UnsetQuotaResponse(quota_scope=dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
