"""REST v2 handler for the session domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, QueryParam
from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    EnqueueSessionInput,
    GetSessionLogsQuery,
    ShutdownSessionServiceInput,
    StartSessionServiceInput,
    TerminateSessionsInput,
    UpdateSessionInput,
)
from ai.backend.common.dto.manager.v2.session.request import (
    SessionIdPathParam as SessionIdPathParamDTO,
)
from ai.backend.common.types import AgentId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import (
    AgentIdPathParam,
    ProjectIdPathParam,
    SessionIdPathParam,
)
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.session import SessionAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2SessionHandler:
    """REST v2 handler for session and kernel operations."""

    def __init__(self, *, adapter: SessionAdapter) -> None:
        self._adapter = adapter

    async def enqueue(
        self,
        user_ctx: UserContext,
        body: BodyParam[EnqueueSessionInput],
    ) -> APIResponse:
        """Enqueue a new compute session."""
        result = await self._adapter.enqueue(
            body.parsed,
            user_id=user_ctx.user_uuid,
            user_role=user_ctx.user_role,
            access_key=user_ctx.access_key,
            domain_name=user_ctx.user_domain,
            group_id=body.parsed.project_id,
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

    async def get(
        self,
        path: PathParam[SessionIdPathParamDTO],
    ) -> APIResponse:
        """Get a single session by ID."""
        result = await self._adapter.get(path.parsed.session_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(
        self,
        body: BodyParam[AdminSearchSessionsInput],
    ) -> APIResponse:
        """Search sessions owned by the current user."""
        result = await self._adapter.my_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def project_search(
        self,
        path: PathParam[ProjectIdPathParam],
        body: BodyParam[AdminSearchSessionsInput],
    ) -> APIResponse:
        """Search sessions within a project."""
        result = await self._adapter.project_search(path.parsed.project_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def terminate(
        self,
        body: BodyParam[TerminateSessionsInput],
    ) -> APIResponse:
        """Terminate one or more sessions."""
        result = await self._adapter.terminate(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def start_service(
        self,
        user_ctx: UserContext,
        path: PathParam[SessionIdPathParamDTO],
        body: BodyParam[StartSessionServiceInput],
    ) -> APIResponse:
        """Start a service in a session."""
        result = await self._adapter.start_service(
            path.parsed.session_id, body.parsed, access_key=user_ctx.access_key
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def shutdown_service(
        self,
        user_ctx: UserContext,
        path: PathParam[SessionIdPathParamDTO],
        body: BodyParam[ShutdownSessionServiceInput],
    ) -> APIResponse:
        """Shut down a service in a session."""
        await self._adapter.shutdown_service(
            path.parsed.session_id, body.parsed, access_key=user_ctx.access_key
        )
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    async def get_logs(
        self,
        user_ctx: UserContext,
        path: PathParam[SessionIdPathParamDTO],
        query: QueryParam[GetSessionLogsQuery],
    ) -> APIResponse:
        """Get container logs for a session."""
        result = await self._adapter.get_logs(
            path.parsed.session_id,
            access_key=user_ctx.access_key,
            kernel_id=query.parsed.kernel_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        user_ctx: UserContext,
        path: PathParam[SessionIdPathParamDTO],
        body: BodyParam[UpdateSessionInput],
    ) -> APIResponse:
        """Update a session."""
        result = await self._adapter.update(
            path.parsed.session_id, body.parsed, access_key=user_ctx.access_key
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
