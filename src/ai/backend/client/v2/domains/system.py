from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.system import SystemVersionResponse


class SystemClient(BaseDomainClient):
    """Client for system version info endpoint."""

    async def get_versions(self) -> SystemVersionResponse:
        return await self._client.typed_request(
            "GET",
            "/",
            response_model=SystemVersionResponse,
        )
