"""Compute sessions handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.compute_session import (
    PaginationInfo,
    SearchComputeSessionsRequest,
    SearchComputeSessionsResponse,
)
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.session.actions.search_kernel import SearchKernelsAction
from ai.backend.manager.services.session.processors import SessionProcessors

from .adapter import ComputeSessionsAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ComputeSessionsHandler:
    """Compute sessions API handler with constructor-injected dependencies."""

    def __init__(self, *, session: SessionProcessors) -> None:
        self._session = session
        self._adapter = ComputeSessionsAdapter()

    async def search_sessions(
        self,
        body: BodyParam[SearchComputeSessionsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search compute sessions with nested container data."""
        log.info("SEARCH_SESSIONS (ak:{})", ctx.access_key)

        # Step 1: Search sessions
        session_querier = self._adapter.build_session_querier(body.parsed)
        session_result = await self._session.search_sessions.wait_for_complete(
            SearchSessionsAction(querier=session_querier)
        )

        # Step 2: Fetch kernels for found sessions
        session_ids = [SessionId(s.id) for s in session_result.data]
        kernels_by_session = {}
        if session_ids:
            kernel_querier = self._adapter.build_kernel_querier_for_sessions(session_ids)
            kernel_result = await self._session.search_kernels.wait_for_complete(
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
