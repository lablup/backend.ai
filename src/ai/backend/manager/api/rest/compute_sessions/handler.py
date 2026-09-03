"""Compute sessions handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.compute_session import (
    PaginationInfo,
    SearchComputeSessionsRequest,
    SearchComputeSessionsResponse,
)
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.services.session.actions.batch_get_session_resource_allocation import (
    BatchGetSessionResourceAllocationAction,
)
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

        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")

        # Step 1: Search sessions
        session_querier = self._adapter.build_session_querier(body.parsed)
        session_result = await self._session.search_sessions.run(
            SearchSessionsAction(querier=session_querier, user_id=UserID(user.user_id))
        )

        # Step 2: Fetch kernels for found sessions
        session_ids = [SessionId(s.id) for s in session_result.data]
        kernels_by_session = {}
        if session_ids:
            kernel_querier = self._adapter.build_kernel_querier_for_sessions(session_ids)
            kernel_result = await self._session.search_kernels.run(
                SearchKernelsAction(querier=kernel_querier, user_id=UserID(user.user_id))
            )
            kernels_by_session = self._adapter.group_kernels_by_session(kernel_result.data)

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
