"""V2 SDK client for the system session environ domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    ListSystemSessionEnvironValueSourcesPayload,
)

_PATH = "/v2/system-session-environs"


class V2SystemSessionEnvironClient(BaseDomainClient):
    """SDK client for the system session environ domain."""

    async def list_value_sources(self) -> ListSystemSessionEnvironValueSourcesPayload:
        """List every value source a system session environ row can carry."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/value-sources",
            response_model=ListSystemSessionEnvironValueSourcesPayload,
        )
