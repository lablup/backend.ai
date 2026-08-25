"""V2 SDK client for the scope operation catalog."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.scope_operation.response import ListScopeOperationsPayload

_PATH = "/v2/scope-operations"


class V2ScopeOperationClient(BaseDomainClient):
    """SDK client for ``/v2/scope-operations`` endpoints."""

    async def list(self) -> ListScopeOperationsPayload:
        """List every operation the wiring targets by scope."""
        return await self._client.typed_request(
            "GET",
            _PATH,
            response_model=ListScopeOperationsPayload,
        )
