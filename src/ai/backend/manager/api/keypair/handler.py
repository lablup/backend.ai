"""
REST API handlers for keypair system.
Provides CRUD endpoints for API keypair management.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.keypair import (
    CreateKeyPairRequest,
    CreateKeyPairResponse,
    DeleteKeyPairRequest,
    DeleteKeyPairResponse,
    GetKeyPairResponse,
    PaginationInfo,
    SearchKeyPairsRequest,
    SearchKeyPairsResponse,
    UpdateKeyPairRequest,
    UpdateKeyPairResponse,
)
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.keypair_request import (
    ActivateKeyPairPathParam,
    DeactivateKeyPairPathParam,
    GetKeyPairPathParam,
    UpdateKeyPairPathParam,
)
from ai.backend.manager.services.keypair.actions import (
    ActivateKeyPairAction,
    CreateKeyPairAction,
    DeactivateKeyPairAction,
    DeleteKeyPairAction,
    GetKeyPairAction,
    SearchKeyPairsAction,
    UpdateKeyPairAction,
)

from .adapter import KeyPairAdapter

__all__ = ("create_app",)


class KeyPairAPIHandler:
    """REST API handler class for keypair operations."""

    def __init__(self) -> None:
        self.adapter = KeyPairAdapter()

    @auth_required_for_method
    @api_handler
    async def create(
        self,
        body: BodyParam[CreateKeyPairRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new keypair."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can create keypairs.")

        action_result = await processors.keypair.create.wait_for_complete(
            CreateKeyPairAction(
                user_id=body.parsed.user_id,
                is_active=body.parsed.is_active,
                is_admin=body.parsed.is_admin,
                resource_policy=body.parsed.resource_policy,
                rate_limit=body.parsed.rate_limit,
            )
        )

        resp = CreateKeyPairResponse(
            keypair=self.adapter.convert_to_dto(action_result.keypair_data),
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetKeyPairPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific keypair."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can get keypairs.")

        action_result = await processors.keypair.get.wait_for_complete(
            GetKeyPairAction(access_key=path.parsed.access_key)
        )

        resp = GetKeyPairResponse(
            keypair=self.adapter.convert_to_dto(action_result.keypair_data),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchKeyPairsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search keypairs with filters, orders, and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can search keypairs.")

        querier = self.adapter.build_querier(body.parsed)

        action_result = await processors.keypair.search.wait_for_complete(
            SearchKeyPairsAction(querier=querier)
        )

        resp = SearchKeyPairsResponse(
            keypairs=[self.adapter.convert_to_dto(kp) for kp in action_result.keypairs],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update(
        self,
        path: PathParam[UpdateKeyPairPathParam],
        body: BodyParam[UpdateKeyPairRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing keypair."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can update keypairs.")

        access_key = path.parsed.access_key
        action_result = await processors.keypair.update.wait_for_complete(
            UpdateKeyPairAction(updater=self.adapter.build_updater(body.parsed, access_key))
        )

        resp = UpdateKeyPairResponse(
            keypair=self.adapter.convert_to_dto(action_result.keypair_data),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete(
        self,
        body: BodyParam[DeleteKeyPairRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete keypairs."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can delete keypairs.")

        action_result = await processors.keypair.delete.wait_for_complete(
            DeleteKeyPairAction(access_keys=body.parsed.access_keys)
        )

        resp = DeleteKeyPairResponse(deleted=action_result.deleted)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def activate(
        self,
        path: PathParam[ActivateKeyPairPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Activate a keypair."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can activate keypairs.")

        action_result = await processors.keypair.activate.wait_for_complete(
            ActivateKeyPairAction(access_key=path.parsed.access_key)
        )

        resp = UpdateKeyPairResponse(
            keypair=self.adapter.convert_to_dto(action_result.keypair_data),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def deactivate(
        self,
        path: PathParam[DeactivateKeyPairPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Deactivate a keypair."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can deactivate keypairs.")

        action_result = await processors.keypair.deactivate.wait_for_complete(
            DeactivateKeyPairAction(access_key=path.parsed.access_key)
        )

        resp = UpdateKeyPairResponse(
            keypair=self.adapter.convert_to_dto(action_result.keypair_data),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for keypair API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/keypairs"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = KeyPairAPIHandler()

    cors.add(app.router.add_route("POST", "", api_handler.create))
    cors.add(app.router.add_route("GET", "/{access_key}", api_handler.get))
    cors.add(app.router.add_route("POST", "/search", api_handler.search))
    cors.add(app.router.add_route("PATCH", "/{access_key}", api_handler.update))
    cors.add(app.router.add_route("POST", "/delete", api_handler.delete))
    cors.add(app.router.add_route("POST", "/{access_key}/activate", api_handler.activate))
    cors.add(app.router.add_route("POST", "/{access_key}/deactivate", api_handler.deactivate))

    return app, []
