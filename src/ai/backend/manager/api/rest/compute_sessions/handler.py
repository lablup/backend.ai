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
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.session.actions.batch_get_session_resource_allocation import (
    BatchGetSessionResourceAllocationAction,
)
from ai.backend.manager.services.session.actions.global_search import GlobalSearchSessionsAction
from ai.backend.manager.services.session.actions.global_search_kernels import (
    GlobalSearchKernelsAction,
)
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

        # Step 1: Search sessions
        session_result = await self._session.global_search.run(
            GlobalSearchSessionsAction(
                searcher=GlobalSearcher(
                    used_by=(), searcher=self._adapter.build_session_searcher(body.parsed)
                )
            )
        )
        sessions = [item.to_session_data() for item in session_result.items]

        # Step 2: Fetch kernels for found sessions
        session_ids = [SessionId(s.id) for s in sessions]
        kernels_by_session = {}
        if session_ids:
            kernel_result = await self._session.global_search_kernels.run(
                GlobalSearchKernelsAction(
                    searcher=GlobalSearcher(
                        used_by=(),
                        searcher=self._adapter.build_kernel_searcher_for_sessions(session_ids),
                    )
                )
            )
            kernels_by_session = self._adapter.group_kernels_by_session(kernel_result.items)

        # Step 3: Aggregate the slot amounts from resource_allocations
        allocations: dict[SessionId, ResourceAllocationAggregate] = {}
        if session_ids:
            allocation_result = await self._session.batch_get_session_resource_allocation.run(
                BatchGetSessionResourceAllocationAction(session_ids=session_ids)
            )
            allocations = {
                SessionId(item.entity_id): item.value
                for item in allocation_result.items
                if item.value is not None
            }

        # Step 4: Convert to DTOs
        items = [
            self._adapter.convert_session_to_dto(
                session,
                allocations.get(SessionId(session.id)),
                kernels_by_session.get(session.id, []),
            )
            for session in sessions
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
