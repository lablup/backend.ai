"""REST v2 handler for the session domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    CreateSessionInput,
)
from ai.backend.common.types import AgentId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import AgentIdPathParam, SessionIdPathParam
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.session import SessionAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2SessionHandler:
    """REST v2 handler for session and kernel operations."""

    def __init__(self, *, adapter: SessionAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        user_ctx: UserContext,
        body: BodyParam[CreateSessionInput],
    ) -> APIResponse:
        """Create a new compute session."""
        result = await self._adapter.create(
            body.parsed,
            user_id=user_ctx.user_uuid,
            user_role=user_ctx.user_role,
            access_key=user_ctx.access_key,
            domain_name=user_ctx.user_domain,
            group_id=body.parsed.project_id or user_ctx.user_uuid,
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_search_sessions(
        self,
        body: BodyParam[AdminSearchSessionsInput],
    ) -> APIResponse:
        """Search sessions with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_kernels(
        self,
        body: BodyParam[AdminSearchKernelsInput],
    ) -> APIResponse:
        """Search kernels with admin scope."""
        result = await self._adapter.admin_search_kernels(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_sessions_by_agent(
        self,
        path: PathParam[AgentIdPathParam],
        body: BodyParam[AdminSearchSessionsInput],
    ) -> APIResponse:
        """Search sessions scoped to a specific agent."""
        result = await self._adapter.search_sessions_by_agent(
            AgentId(path.parsed.agent_id), body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_kernels_by_agent(
        self,
        path: PathParam[AgentIdPathParam],
        body: BodyParam[AdminSearchKernelsInput],
    ) -> APIResponse:
        """Search kernels scoped to a specific agent."""
        result = await self._adapter.search_kernels_by_agent(
            AgentId(path.parsed.agent_id), body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_kernels_by_session(
        self,
        path: PathParam[SessionIdPathParam],
        body: BodyParam[AdminSearchKernelsInput],
    ) -> APIResponse:
        """Search kernels scoped to a specific session."""
        result = await self._adapter.search_kernels_by_session(
            SessionId(path.parsed.session_id), body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
