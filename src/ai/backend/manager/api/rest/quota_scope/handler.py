"""Quota scope handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

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
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.quota_scope_request import GetQuotaScopePathParam

from .adapter import QuotaScopeAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class QuotaScopeHandler:
    """Quota scope API handler with constructor-injected dependencies."""

    def __init__(self, *, storage_manager: StorageSessionManager) -> None:
        self._storage_manager = storage_manager
        self._adapter = QuotaScopeAdapter()

    async def get(
        self,
        path: PathParam[GetQuotaScopePathParam],
        ctx: UserContext,
    ) -> APIResponse:
        """Get a single quota scope by storage host and scope ID."""
        log.info("GET (ak:{})", ctx.access_key)
        storage_host_name = path.parsed.storage_host_name
        quota_scope_id = path.parsed.quota_scope_id
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(storage_host_name)
        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        quota_config = await manager_client.get_quota_scope(volume_name, quota_scope_id)
        dto = self._adapter.convert_to_dto(quota_scope_id, storage_host_name, quota_config)
        resp = GetQuotaScopeResponse(quota_scope=dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search(
        self,
        body: BodyParam[SearchQuotaScopesRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search all quota scopes across all volumes."""
        log.info("SEARCH (ak:{})", ctx.access_key)
        all_volumes = await self._storage_manager.get_all_volumes()
        quota_scopes: list[QuotaScopeDTO] = []
        for host, volume_info in all_volumes:
            proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(host)
            manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
            try:
                quota_config = await manager_client.get_quota_scope(volume_name, "")
                dto = self._adapter.convert_to_dto("", host, quota_config)
                quota_scopes.append(dto)
            except Exception:
                pass
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
        storage_host_name = body.parsed.storage_host_name
        quota_scope_id = body.parsed.quota_scope_id
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(storage_host_name)
        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.update_quota_scope(
            volume_name,
            quota_scope_id,
            body.parsed.hard_limit_bytes,
        )
        quota_config = await manager_client.get_quota_scope(volume_name, quota_scope_id)
        dto = self._adapter.convert_to_dto(quota_scope_id, storage_host_name, quota_config)
        resp = SetQuotaResponse(quota_scope=dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def unset_quota(
        self,
        body: BodyParam[UnsetQuotaRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Unset (remove) quota limit for a scope."""
        log.info("UNSET_QUOTA (ak:{})", ctx.access_key)
        storage_host_name = body.parsed.storage_host_name
        quota_scope_id = body.parsed.quota_scope_id
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(storage_host_name)
        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.delete_quota_scope_quota(volume_name, quota_scope_id)
        dto = QuotaScopeDTO(
            quota_scope_id=quota_scope_id,
            storage_host_name=storage_host_name,
            usage_bytes=None,
            usage_count=None,
            hard_limit_bytes=None,
        )
        resp = UnsetQuotaResponse(quota_scope=dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
