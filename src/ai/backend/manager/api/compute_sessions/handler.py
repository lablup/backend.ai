"""
REST API handlers for compute sessions.
Provides search and detail endpoints for compute sessions with nested container data.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus
from uuid import UUID

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.compute_session import (
    ComputeSessionPathParam,
    GetComputeSessionDetailResponse,
    PaginationInfo,
    SearchComputeSessionsRequest,
    SearchComputeSessionsResponse,
)
from ai.backend.common.types import SessionId
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.scheduler.options import SessionConditions
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction

from .adapter import ComputeSessionsAdapter

__all__ = ("create_app",)


class ComputeSessionsAPIHandler:
    """REST API handler class for compute session operations."""

    def __init__(self) -> None:
        self._adapter = ComputeSessionsAdapter()

    @auth_required_for_method
    @api_handler
    async def search_sessions(
        self,
        body: BodyParam[SearchComputeSessionsRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search compute sessions with nested container data."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can list compute sessions.")

        # Step 1: Search sessions
        session_querier = self._adapter.build_session_querier(body.parsed)
        session_result = await processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=session_querier)
        )

        # Step 2: Fetch kernels for found sessions
        session_ids = [SessionId(s.id) for s in session_result.data]
        kernels_by_session = {}
        if session_ids:
            kernel_querier = self._adapter.build_kernel_querier_for_sessions(session_ids)
            kernel_result = await processors.session.search_kernels.wait_for_complete(
                SearchKernelsAction(querier=kernel_querier)
            )
            kernels_by_session = self._adapter.group_kernels_by_session(kernel_result.data)

        # Step 3: Convert to DTOs
        items = [
            self._adapter.convert_session_to_dto(session, kernels_by_session.get(session.id, []))
            for session in session_result.data
        ]

        resp = SearchComputeSessionsResponse(
            items=items,
            pagination=PaginationInfo(
                total=session_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_session_detail(
        self,
        path: PathParam[ComputeSessionPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a single compute session detail with nested containers."""
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can get compute session details.")

        session_id = SessionId(UUID(path.parsed.session_id))

        # Step 1: Find the session by ID
        querier = BatchQuerier(
            conditions=[SessionConditions.by_ids([session_id])],
            orders=[],
            pagination=NoPagination(),
        )
        session_result = await processors.session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=querier)
        )
        if not session_result.data:
            raise web.HTTPNotFound(reason=f"Compute session {path.parsed.session_id} not found.")

        session = session_result.data[0]

        # Step 2: Fetch kernels for this session
        kernel_querier = self._adapter.build_kernel_querier_for_sessions([session_id])
        kernel_result = await processors.session.search_kernels.wait_for_complete(
            SearchKernelsAction(querier=kernel_querier)
        )
        kernels_by_session = self._adapter.group_kernels_by_session(kernel_result.data)

        # Step 3: Convert to DTO
        session_dto = self._adapter.convert_session_to_dto(
            session, kernels_by_session.get(session.id, [])
        )

        resp = GetComputeSessionDetailResponse(session=session_dto)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for compute sessions API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "compute-sessions"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = ComputeSessionsAPIHandler()

    cors.add(app.router.add_route("POST", "/search", api_handler.search_sessions))
    cors.add(app.router.add_route("GET", "/{session_id}", api_handler.get_session_detail))

    return app, []
