from __future__ import annotations

from typing import Any

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel


class StartServiceRequest(BaseRequestModel):
    """Request body for POST /sessions/{session_name}/start-service."""

    app: str
    port: int | None = None
    envs: str | None = None
    arguments: str | None = None
    login_session_token: str | None = None


class StartServiceResponse(BaseResponseModel):
    """Response body from POST /sessions/{session_name}/start-service."""

    token: str
    wsproxy_addr: str


class ShutdownServiceRequest(BaseRequestModel):
    """Request body for POST /sessions/{session_name}/shutdown-service."""

    service_name: str


class GetStreamAppsResponseItem(BaseResponseModel):
    """Single item in the response list from GET /stream/session/{name}/apps.

    Re-uses the same field definitions as :class:`StreamAppInfo` but inherits
    from ``BaseResponseModel`` so it can be used with ``typed_request_list()``.
    """

    name: str
    protocol: str
    ports: list[int]
    url_template: str | None = None
    allowed_arguments: dict[str, Any] | None = None
    allowed_envs: dict[str, Any] | None = None


class StreamingClient(BaseDomainClient):
    """SDK v2 client for Backend.AI streaming REST endpoints.

    WebSocket and SSE endpoints are deferred until the base client
    provides ``connect_websocket()`` / ``connect_sse()`` infrastructure.
    """

    async def get_stream_apps(self, session_name: str) -> list[GetStreamAppsResponseItem]:
        """List available streaming apps/services for a session.

        ``GET /stream/session/{session_name}/apps``
        """
        return await self._client.typed_request_list(
            "GET",
            f"/stream/session/{session_name}/apps",
            response_model=GetStreamAppsResponseItem,
        )

    async def start_service(
        self,
        session_name: str,
        request: StartServiceRequest,
    ) -> StartServiceResponse:
        """Start a service (app) in a session.

        ``POST /sessions/{session_name}/start-service``
        """
        return await self._client.typed_request(
            "POST",
            f"/sessions/{session_name}/start-service",
            request=request,
            response_model=StartServiceResponse,
        )

    async def shutdown_service(
        self,
        session_name: str,
        request: ShutdownServiceRequest,
    ) -> None:
        """Shutdown a running service in a session.

        ``POST /sessions/{session_name}/shutdown-service``
        """
        await self._client._request_no_content(
            "POST",
            f"/sessions/{session_name}/shutdown-service",
            json=request.model_dump(exclude_none=True),
        )
