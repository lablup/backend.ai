"""V2 REST SDK client for the session domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput
from ai.backend.common.dto.manager.v2.kernel.response import AdminSearchKernelsPayload
from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput
from ai.backend.common.dto.manager.v2.session.response import AdminSearchSessionsPayload

_PATH = "/v2/sessions"


class V2SessionClient(BaseDomainClient):
    """SDK client for the ``/v2/sessions`` REST endpoints."""

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
            f"{_PATH}/search-by-agent/{agent_id}",
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
            f"{_PATH}/kernels/search-by-agent/{agent_id}",
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
