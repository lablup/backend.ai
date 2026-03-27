"""V2 REST SDK client for the session domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
from ai.backend.common.dto.manager.v2.kernel.response import AdminSearchKernelsPayload
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    EnqueueSessionInput,
    ShutdownSessionServiceInput,
    StartSessionServiceInput,
    TerminateSessionsInput,
    UpdateSessionInput,
)
from ai.backend.common.dto.manager.v2.session.response import (
    AdminSearchSessionsPayload,
    EnqueueSessionPayload,
    SessionLogsPayload,
    SessionNode,
    StartSessionServicePayload,
    TerminateSessionsPayload,
    UpdateSessionPayload,
)

_PATH = "/v2/sessions"


class V2SessionClient(BaseDomainClient):
    """SDK client for the ``/v2/sessions`` REST endpoints."""

    async def enqueue(
        self,
        request: EnqueueSessionInput,
    ) -> EnqueueSessionPayload:
        """Enqueue a new compute session."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/enqueue",
            request=request,
            response_model=EnqueueSessionPayload,
        )

    async def admin_search(
        self,
        request: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search sessions with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchSessionsPayload,
        )

    async def admin_search_kernels(
        self,
        request: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search kernels with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/kernels/search",
            request=request,
            response_model=AdminSearchKernelsPayload,
        )

    async def search_sessions_by_agent(
        self,
        agent_id: str,
        request: AdminSearchSessionsInput,
    ) -> AdminSearchSessionsPayload:
        """Search sessions scoped to a specific agent."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/agents/{agent_id}/search",
            request=request,
            response_model=AdminSearchSessionsPayload,
        )

    async def search_kernels_by_agent(
        self,
        agent_id: str,
        request: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search kernels scoped to a specific agent."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/kernels/agents/{agent_id}/search",
            request=request,
            response_model=AdminSearchKernelsPayload,
        )

    async def search_kernels_by_session(
        self,
        session_id: str,
        request: AdminSearchKernelsInput,
    ) -> AdminSearchKernelsPayload:
        """Search kernels scoped to a specific session."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{session_id}/kernels/search",
            request=request,
            response_model=AdminSearchKernelsPayload,
        )

    async def get(self, session_id: UUID) -> SessionNode:
        """Get a single session by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{session_id}",
            response_model=SessionNode,
        )

    async def my_search(self, request: AdminSearchSessionsInput) -> AdminSearchSessionsPayload:
        """Search my sessions."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=AdminSearchSessionsPayload,
        )

    async def project_search(
        self, project_id: UUID, request: AdminSearchSessionsInput
    ) -> AdminSearchSessionsPayload:
        """Search sessions within a project."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/{project_id}/search",
            request=request,
            response_model=AdminSearchSessionsPayload,
        )

    async def terminate(
        self,
        request: TerminateSessionsInput,
    ) -> TerminateSessionsPayload:
        """Terminate one or more sessions."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/terminate",
            request=request,
            response_model=TerminateSessionsPayload,
        )

    async def start_service(
        self,
        session_id: UUID,
        request: StartSessionServiceInput,
    ) -> StartSessionServicePayload:
        """Start a service in a session."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{session_id}/services/start",
            request=request,
            response_model=StartSessionServicePayload,
        )

    async def shutdown_service(
        self,
        session_id: UUID,
        request: ShutdownSessionServiceInput,
    ) -> None:
        """Shut down a service in a session."""
        await self._client.typed_request_no_content(
            "POST",
            f"{_PATH}/{session_id}/services/shutdown",
            request=request,
        )

    async def get_logs(
        self,
        session_id: UUID,
        kernel_id: UUID | None = None,
    ) -> SessionLogsPayload:
        """Get container logs for a session."""
        params: dict[str, str] = {}
        if kernel_id is not None:
            params["kernel_id"] = str(kernel_id)
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{session_id}/logs",
            params=params if params else None,
            response_model=SessionLogsPayload,
        )

    async def update(
        self,
        session_id: UUID,
        request: UpdateSessionInput,
    ) -> UpdateSessionPayload:
        """Update a session."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{session_id}",
            request=request,
            response_model=UpdateSessionPayload,
        )
