"""V2 SDK client for the session lifecycle handler registry."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.session_lifecycle_handler.response import (
    ListSessionLifecycleHandlersPayload,
)

_PATH = "/v2/session-lifecycle-handlers"


class V2SessionLifecycleHandlerClient(BaseDomainClient):
    """SDK client for the session lifecycle handler registry."""

    async def admin_list(self) -> ListSessionLifecycleHandlersPayload:
        """List all registered session lifecycle handlers (superadmin only)."""
        return await self._client.typed_request(
            "GET",
            _PATH,
            response_model=ListSessionLifecycleHandlersPayload,
        )
