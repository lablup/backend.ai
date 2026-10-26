"""V2 SDK client for the system session environ domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
    MySearchSystemSessionEnvironsInput,
    ScopedSearchSystemSessionEnvironsInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    AdminSearchSystemSessionEnvironsPayload,
    ScopedSearchSystemSessionEnvironsPayload,
)

_PATH = "/v2/system-session-environs"


class V2SystemSessionEnvironClient(BaseDomainClient):
    """SDK client for the system session environ domain."""

    async def admin_search(
        self, request: AdminSearchSystemSessionEnvironsInput
    ) -> AdminSearchSystemSessionEnvironsPayload:
        """Search every system session environ row, at every scope (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchSystemSessionEnvironsPayload,
        )

    async def scoped_search(
        self, request: ScopedSearchSystemSessionEnvironsInput
    ) -> ScopedSearchSystemSessionEnvironsPayload:
        """Search the system session environ rows the named scopes reach."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/scoped/search",
            request=request,
            response_model=ScopedSearchSystemSessionEnvironsPayload,
        )

    async def my_search(
        self, request: MySearchSystemSessionEnvironsInput
    ) -> ScopedSearchSystemSessionEnvironsPayload:
        """Search the enabled rows bound to public, the caller's domain and their projects."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=ScopedSearchSystemSessionEnvironsPayload,
        )
