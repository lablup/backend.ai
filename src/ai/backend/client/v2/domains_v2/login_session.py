"""V2 SDK client for the login session domain."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.login_session.request import (
    AdminRevokeLoginSessionInput,
    AdminSearchLoginSessionsInput,
    MyRevokeLoginSessionInput,
    MySearchLoginSessionsInput,
)
from ai.backend.common.dto.manager.v2.login_session.response import (
    AdminSearchLoginSessionsPayload,
    MySearchLoginSessionsPayload,
    RevokeLoginSessionPayload,
)

_PATH: Final = "/v2/login-sessions"


class V2LoginSessionClient(BaseDomainClient):
    """SDK client for login session operations."""

    async def admin_search(
        self,
        request: AdminSearchLoginSessionsInput,
    ) -> AdminSearchLoginSessionsPayload:
        """Search login sessions with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchLoginSessionsPayload,
        )

    async def my_search(
        self,
        request: MySearchLoginSessionsInput,
    ) -> MySearchLoginSessionsPayload:
        """Search login sessions for the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=MySearchLoginSessionsPayload,
        )

    async def admin_revoke(
        self,
        request: AdminRevokeLoginSessionInput,
    ) -> RevokeLoginSessionPayload:
        """Revoke a login session with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/revoke",
            request=request,
            response_model=RevokeLoginSessionPayload,
        )

    async def my_revoke(
        self,
        request: MyRevokeLoginSessionInput,
    ) -> RevokeLoginSessionPayload:
        """Revoke a login session for the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/revoke",
            request=request,
            response_model=RevokeLoginSessionPayload,
        )
