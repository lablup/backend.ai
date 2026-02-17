"""
REST API handlers for network management.
Provides CRUD endpoints for networks.
"""

from __future__ import annotations

from collections.abc import Iterable

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.network import (
    CreateNetworkRequest,
    DeleteNetworkRequest,
    SearchNetworksRequest,
    UpdateNetworkRequest,
)
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.network_request import (
    GetNetworkPathParam,
    UpdateNetworkPathParam,
)

from .adapter import NetworkAdapter

__all__ = ("create_app",)


class NetworkAPIHandler:
    """REST API handler class for network operations."""

    def __init__(self) -> None:
        self.adapter = NetworkAdapter()

    @auth_required_for_method
    @api_handler
    async def create(
        self,
        body: BodyParam[CreateNetworkRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new network."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can create networks.")

        _ = body.parsed
        _ = processors_ctx.processors
        raise web.HTTPNotImplemented(reason="Network service is not yet available.")

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetNetworkPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific network."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can get networks.")

        _ = path.parsed
        _ = processors_ctx.processors
        raise web.HTTPNotImplemented(reason="Network service is not yet available.")

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchNetworksRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search networks with filters, orders, and pagination."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can search networks.")

        _ = self.adapter.build_querier(body.parsed)
        _ = processors_ctx.processors
        raise web.HTTPNotImplemented(reason="Network service is not yet available.")

    @auth_required_for_method
    @api_handler
    async def update(
        self,
        path: PathParam[UpdateNetworkPathParam],
        body: BodyParam[UpdateNetworkRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing network."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can update networks.")

        _ = self.adapter.build_updater(body.parsed, path.parsed.network_id)
        _ = processors_ctx.processors
        raise web.HTTPNotImplemented(reason="Network service is not yet available.")

    @auth_required_for_method
    @api_handler
    async def delete(
        self,
        body: BodyParam[DeleteNetworkRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete a network."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can delete networks.")

        _ = body.parsed
        _ = processors_ctx.processors
        raise web.HTTPNotImplemented(reason="Network service is not yet available.")


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for network API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/networks"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = NetworkAPIHandler()

    cors.add(app.router.add_route("POST", "", api_handler.create))
    cors.add(app.router.add_route("GET", "/{network_id}", api_handler.get))
    cors.add(app.router.add_route("POST", "/search", api_handler.search))
    cors.add(app.router.add_route("PATCH", "/{network_id}", api_handler.update))
    cors.add(app.router.add_route("POST", "/delete", api_handler.delete))

    return app, []
