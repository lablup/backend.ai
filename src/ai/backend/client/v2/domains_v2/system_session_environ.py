"""V2 SDK client for the system session environ domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminResolveSystemSessionEnvironInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    ResolveSystemSessionEnvironPayload,
)

_PATH = "/v2/system-session-environs"


class V2SystemSessionEnvironClient(BaseDomainClient):
    """SDK client for the system session environ domain."""

    async def admin_resolve(
        self, request: AdminResolveSystemSessionEnvironInput
    ) -> ResolveSystemSessionEnvironPayload:
        """Read the rows a session in the domain and project receives (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/resolve",
            request=request,
            response_model=ResolveSystemSessionEnvironPayload,
        )
