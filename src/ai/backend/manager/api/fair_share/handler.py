"""
REST API handlers for fair share.
Provides search endpoints for fair share and usage bucket data.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.fair_share import (
    GetDomainFairSharePathParam,
    GetDomainFairShareResponse,
    GetProjectFairSharePathParam,
    GetProjectFairShareResponse,
    GetUserFairSharePathParam,
    GetUserFairShareResponse,
    PaginationInfo,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    SearchDomainUsageBucketsRequest,
    SearchDomainUsageBucketsResponse,
    SearchProjectFairSharesRequest,
    SearchProjectFairSharesResponse,
    SearchProjectUsageBucketsRequest,
    SearchProjectUsageBucketsResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
    SearchUserUsageBucketsRequest,
    SearchUserUsageBucketsResponse,
)
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.services.fair_share.actions import (
    GetDomainFairShareAction,
    GetProjectFairShareAction,
    GetUserFairShareAction,
    SearchDomainFairSharesAction,
    SearchProjectFairSharesAction,
    SearchUserFairSharesAction,
)
from ai.backend.manager.services.resource_usage.actions import (
    SearchDomainUsageBucketsAction,
    SearchProjectUsageBucketsAction,
    SearchUserUsageBucketsAction,
)

from .adapter import FairShareAdapter

__all__ = ("create_app",)


class FairShareAPIHandler:
    """REST API handler class for fair share operations."""

    def __init__(self) -> None:
        self._adapter = FairShareAdapter()

    def _check_superadmin(self) -> None:
        """Check if the current user is a superadmin."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    # Domain Fair Share

    @auth_required_for_method
    @api_handler
    async def get_domain_fair_share(
        self,
        path: PathParam[GetDomainFairSharePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a single domain fair share."""
        self._check_superadmin()
        processors = processors_ctx.processors

        action_result = await processors.fair_share.get_domain_fair_share.wait_for_complete(
            GetDomainFairShareAction(
                resource_group=path.parsed.resource_group, domain_name=path.parsed.domain_name
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_domain_fair_share_to_dto(action_result.data)

        resp = GetDomainFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_domain_fair_shares(
        self,
        body: BodyParam[SearchDomainFairSharesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search domain fair shares."""
        self._check_superadmin()
        processors = processors_ctx.processors

        querier = self._adapter.build_domain_fair_share_querier(body.parsed)

        action_result = await processors.fair_share.search_domain_fair_shares.wait_for_complete(
            SearchDomainFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchDomainFairSharesResponse(
            items=[
                self._adapter.convert_domain_fair_share_to_dto(fs) for fs in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Project Fair Share

    @auth_required_for_method
    @api_handler
    async def get_project_fair_share(
        self,
        path: PathParam[GetProjectFairSharePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a single project fair share."""
        self._check_superadmin()
        processors = processors_ctx.processors

        action_result = await processors.fair_share.get_project_fair_share.wait_for_complete(
            GetProjectFairShareAction(
                resource_group=path.parsed.resource_group, project_id=path.parsed.project_id
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_project_fair_share_to_dto(action_result.data)

        resp = GetProjectFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_project_fair_shares(
        self,
        body: BodyParam[SearchProjectFairSharesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search project fair shares."""
        self._check_superadmin()
        processors = processors_ctx.processors

        querier = self._adapter.build_project_fair_share_querier(body.parsed)

        action_result = await processors.fair_share.search_project_fair_shares.wait_for_complete(
            SearchProjectFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchProjectFairSharesResponse(
            items=[
                self._adapter.convert_project_fair_share_to_dto(fs) for fs in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # User Fair Share

    @auth_required_for_method
    @api_handler
    async def get_user_fair_share(
        self,
        path: PathParam[GetUserFairSharePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a single user fair share."""
        self._check_superadmin()
        processors = processors_ctx.processors

        action_result = await processors.fair_share.get_user_fair_share.wait_for_complete(
            GetUserFairShareAction(
                resource_group=path.parsed.resource_group,
                project_id=path.parsed.project_id,
                user_uuid=path.parsed.user_uuid,
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_user_fair_share_to_dto(action_result.data)

        resp = GetUserFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_user_fair_shares(
        self,
        body: BodyParam[SearchUserFairSharesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search user fair shares."""
        self._check_superadmin()
        processors = processors_ctx.processors

        querier = self._adapter.build_user_fair_share_querier(body.parsed)

        action_result = await processors.fair_share.search_user_fair_shares.wait_for_complete(
            SearchUserFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchUserFairSharesResponse(
            items=[self._adapter.convert_user_fair_share_to_dto(fs) for fs in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Domain Usage Bucket

    @auth_required_for_method
    @api_handler
    async def search_domain_usage_buckets(
        self,
        body: BodyParam[SearchDomainUsageBucketsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search domain usage buckets."""
        self._check_superadmin()
        processors = processors_ctx.processors

        querier = self._adapter.build_domain_usage_bucket_querier(body.parsed)

        action_result = (
            await processors.resource_usage.search_domain_usage_buckets.wait_for_complete(
                SearchDomainUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                )
            )
        )

        resp = SearchDomainUsageBucketsResponse(
            items=[
                self._adapter.convert_domain_usage_bucket_to_dto(b) for b in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Project Usage Bucket

    @auth_required_for_method
    @api_handler
    async def search_project_usage_buckets(
        self,
        body: BodyParam[SearchProjectUsageBucketsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search project usage buckets."""
        self._check_superadmin()
        processors = processors_ctx.processors

        querier = self._adapter.build_project_usage_bucket_querier(body.parsed)

        action_result = (
            await processors.resource_usage.search_project_usage_buckets.wait_for_complete(
                SearchProjectUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                )
            )
        )

        resp = SearchProjectUsageBucketsResponse(
            items=[
                self._adapter.convert_project_usage_bucket_to_dto(b) for b in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # User Usage Bucket

    @auth_required_for_method
    @api_handler
    async def search_user_usage_buckets(
        self,
        body: BodyParam[SearchUserUsageBucketsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search user usage buckets."""
        self._check_superadmin()
        processors = processors_ctx.processors

        querier = self._adapter.build_user_usage_bucket_querier(body.parsed)

        action_result = await processors.resource_usage.search_user_usage_buckets.wait_for_complete(
            SearchUserUsageBucketsAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchUserUsageBucketsResponse(
            items=[self._adapter.convert_user_usage_bucket_to_dto(b) for b in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for fair share API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "fair-share"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = FairShareAPIHandler()

    # Domain fair share routes
    cors.add(
        app.router.add_route(
            "GET",
            "/domains/{resource_group}/{domain_name}",
            api_handler.get_domain_fair_share,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/domains/search",
            api_handler.search_domain_fair_shares,
        )
    )

    # Project fair share routes
    cors.add(
        app.router.add_route(
            "GET",
            "/projects/{resource_group}/{project_id}",
            api_handler.get_project_fair_share,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/projects/search",
            api_handler.search_project_fair_shares,
        )
    )

    # User fair share routes
    cors.add(
        app.router.add_route(
            "GET",
            "/users/{resource_group}/{project_id}/{user_uuid}",
            api_handler.get_user_fair_share,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/users/search",
            api_handler.search_user_fair_shares,
        )
    )

    # Usage bucket routes
    cors.add(
        app.router.add_route(
            "POST",
            "/usage-buckets/domains/search",
            api_handler.search_domain_usage_buckets,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/usage-buckets/projects/search",
            api_handler.search_project_usage_buckets,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/usage-buckets/users/search",
            api_handler.search_user_usage_buckets,
        )
    )

    return app, []
