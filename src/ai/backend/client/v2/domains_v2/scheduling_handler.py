"""V2 SDK client for the scheduling-handler registry."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.scheduling_handler.response import (
    ListSchedulingHandlersPayload,
)

_PATH = "/v2/scheduling-handlers"


class V2SchedulingHandlerClient(BaseDomainClient):
    """SDK client for the deployment scheduling handler registry."""

    async def list(self) -> ListSchedulingHandlersPayload:
        """List all registered deployment scheduling handlers (superadmin only)."""
        return await self._client.typed_request(
            "GET",
            _PATH,
            response_model=ListSchedulingHandlersPayload,
        )
