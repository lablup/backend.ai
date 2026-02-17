"""
REST API handlers for domain management.
Provides CRUD endpoints for domain (tenant) operations.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    DeleteDomainRequest,
    DeleteDomainResponse,
    GetDomainResponse,
    PaginationInfo,
    PurgeDomainRequest,
    PurgeDomainResponse,
    SearchDomainsRequest,
    SearchDomainsResponse,
    UpdateDomainRequest,
    UpdateDomainResponse,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.data.domain.types import UserInfo
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.domain_request import (
    GetDomainPathParam,
    UpdateDomainPathParam,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction
from ai.backend.manager.services.domain.actions.get_domain import GetDomainAction
from ai.backend.manager.services.domain.actions.modify_domain import ModifyDomainAction
from ai.backend.manager.services.domain.actions.purge_domain import PurgeDomainAction
from ai.backend.manager.services.domain.actions.search_domains import SearchDomainsAction

from .adapter import DomainAdapter

__all__ = ("create_app",)


class DomainAPIHandler:
    """REST API handler class for domain operations."""

    def __init__(self) -> None:
        self.adapter = DomainAdapter()

    @auth_required_for_method
    @api_handler
    async def create(
        self,
        body: BodyParam[CreateDomainRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create a new domain."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can create domains.")

        creator = Creator(
            spec=DomainCreatorSpec(
                name=body.parsed.name,
                description=body.parsed.description,
                is_active=body.parsed.is_active,
                total_resource_slots=(
                    ResourceSlot(body.parsed.total_resource_slots)
                    if body.parsed.total_resource_slots is not None
                    else None
                ),
                allowed_vfolder_hosts=body.parsed.allowed_vfolder_hosts,
                allowed_docker_registries=body.parsed.allowed_docker_registries,
                integration_id=body.parsed.integration_id,
            )
        )
        user_info = UserInfo(
            id=me.user_id,
            role=me.role,
            domain_name=me.domain_name,
        )

        action_result = await processors.domain.create_domain.wait_for_complete(
            CreateDomainAction(creator=creator, user_info=user_info)
        )

        resp = CreateDomainResponse(domain=self.adapter.convert_to_dto(action_result.domain_data))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetDomainPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific domain by name."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can get domains.")

        action_result = await processors.domain.get_domain.wait_for_complete(
            GetDomainAction(domain_name=path.parsed.domain_name)
        )

        resp = GetDomainResponse(domain=self.adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchDomainsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search domains with filters, orders, and pagination."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can search domains.")

        querier = self.adapter.build_querier(body.parsed)

        action_result = await processors.domain.search_domains.wait_for_complete(
            SearchDomainsAction(querier=querier)
        )

        resp = SearchDomainsResponse(
            domains=[self.adapter.convert_to_dto(d) for d in action_result.items],
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
        path: PathParam[UpdateDomainPathParam],
        body: BodyParam[UpdateDomainRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update an existing domain."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can update domains.")

        domain_name = path.parsed.domain_name
        updater = self.adapter.build_updater(body.parsed, domain_name)
        user_info = UserInfo(
            id=me.user_id,
            role=me.role,
            domain_name=me.domain_name,
        )

        action_result = await processors.domain.modify_domain.wait_for_complete(
            ModifyDomainAction(user_info=user_info, updater=updater)
        )

        resp = UpdateDomainResponse(domain=self.adapter.convert_to_dto(action_result.domain_data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete(
        self,
        body: BodyParam[DeleteDomainRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Delete (soft-delete) a domain."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can delete domains.")

        user_info = UserInfo(
            id=me.user_id,
            role=me.role,
            domain_name=me.domain_name,
        )

        await processors.domain.delete_domain.wait_for_complete(
            DeleteDomainAction(name=body.parsed.name, user_info=user_info)
        )

        resp = DeleteDomainResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def purge(
        self,
        body: BodyParam[PurgeDomainRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Permanently purge a domain."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can purge domains.")

        user_info = UserInfo(
            id=me.user_id,
            role=me.role,
            domain_name=me.domain_name,
        )

        await processors.domain.purge_domain.wait_for_complete(
            PurgeDomainAction(name=body.parsed.name, user_info=user_info)
        )

        resp = PurgeDomainResponse(purged=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for domain API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/domains"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    handler = DomainAPIHandler()

    # Domain routes
    cors.add(app.router.add_route("POST", "", handler.create))
    cors.add(app.router.add_route("GET", "/{domain_name}", handler.get))
    cors.add(app.router.add_route("POST", "/search", handler.search))
    cors.add(app.router.add_route("PATCH", "/{domain_name}", handler.update))
    cors.add(app.router.add_route("POST", "/delete", handler.delete))
    cors.add(app.router.add_route("POST", "/purge", handler.purge))

    return app, []
