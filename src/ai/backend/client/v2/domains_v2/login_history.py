"""V2 SDK client for the login history domain."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.login_history.request import (
    AdminSearchLoginHistoryInput,
    MySearchLoginHistoryInput,
)
from ai.backend.common.dto.manager.v2.login_history.response import (
    AdminSearchLoginHistoryPayload,
    MySearchLoginHistoryPayload,
)

_PATH: Final = "/v2/login-history"


class V2LoginHistoryClient(BaseDomainClient):
    """SDK client for login history operations."""

    async def admin_search(
        self,
        request: AdminSearchLoginHistoryInput,
    ) -> AdminSearchLoginHistoryPayload:
        """Search login history with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchLoginHistoryPayload,
        )

    async def my_search(
        self,
        request: MySearchLoginHistoryInput,
    ) -> MySearchLoginHistoryPayload:
        """Search login history for the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=MySearchLoginHistoryPayload,
        )
