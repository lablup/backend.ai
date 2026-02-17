from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
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
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.dto.context import StorageSessionManagerCtx
from ai.backend.manager.dto.quota_scope_request import GetQuotaScopePathParam

from .adapter import QuotaScopeAdapter

__all__ = ("create_app",)


class QuotaScopeAPIHandler:
    def __init__(self) -> None:
        self.adapter = QuotaScopeAdapter()

    def _check_superadmin(self) -> None:
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can manage quota scopes.")

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetQuotaScopePathParam],
        storage_ctx: StorageSessionManagerCtx,
    ) -> APIResponse:
        self._check_superadmin()
        storage_manager = storage_ctx.storage_manager
        storage_host_name = path.parsed.storage_host_name
        quota_scope_id = path.parsed.quota_scope_id
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(storage_host_name)
        manager_client = storage_manager.get_manager_facing_client(proxy_name)
        quota_config = await manager_client.get_quota_scope(volume_name, quota_scope_id)
        dto = self.adapter.convert_to_dto(quota_scope_id, storage_host_name, quota_config)
        resp = GetQuotaScopeResponse(quota_scope=dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchQuotaScopesRequest],
        storage_ctx: StorageSessionManagerCtx,
    ) -> APIResponse:
        self._check_superadmin()
        storage_manager = storage_ctx.storage_manager
        all_volumes = await storage_manager.get_all_volumes()
        quota_scopes: list[QuotaScopeDTO] = []
        for host, volume_info in all_volumes:
            proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(host)
            manager_client = storage_manager.get_manager_facing_client(proxy_name)
            try:
                quota_config = await manager_client.get_quota_scope(volume_name, "")
                dto = self.adapter.convert_to_dto("", host, quota_config)
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

    @auth_required_for_method
    @api_handler
    async def set_quota(
        self,
        body: BodyParam[SetQuotaRequest],
        storage_ctx: StorageSessionManagerCtx,
    ) -> APIResponse:
        self._check_superadmin()
        storage_manager = storage_ctx.storage_manager
        storage_host_name = body.parsed.storage_host_name
        quota_scope_id = body.parsed.quota_scope_id
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(storage_host_name)
        manager_client = storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.update_quota_scope(
            volume_name,
            quota_scope_id,
            body.parsed.hard_limit_bytes,
        )
        quota_config = await manager_client.get_quota_scope(volume_name, quota_scope_id)
        dto = self.adapter.convert_to_dto(quota_scope_id, storage_host_name, quota_config)
        resp = SetQuotaResponse(quota_scope=dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def unset_quota(
        self,
        body: BodyParam[UnsetQuotaRequest],
        storage_ctx: StorageSessionManagerCtx,
    ) -> APIResponse:
        self._check_superadmin()
        storage_manager = storage_ctx.storage_manager
        storage_host_name = body.parsed.storage_host_name
        quota_scope_id = body.parsed.quota_scope_id
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(storage_host_name)
        manager_client = storage_manager.get_manager_facing_client(proxy_name)
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


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/quota-scopes"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    handler = QuotaScopeAPIHandler()

    cors.add(
        app.router.add_route(
            "GET",
            "/{storage_host_name}/{quota_scope_id}",
            handler.get,
        )
    )
    cors.add(app.router.add_route("POST", "/search", handler.search))
    cors.add(app.router.add_route("POST", "/set", handler.set_quota))
    cors.add(app.router.add_route("POST", "/unset", handler.unset_quota))

    return app, []
