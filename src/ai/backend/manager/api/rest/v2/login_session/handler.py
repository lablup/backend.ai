"""REST v2 handler for the login session domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.login_session.request import (
    AdminRevokeLoginSessionInput,
    AdminSearchLoginSessionsInput,
    AdminUnblockUserInput,
    MyRevokeLoginSessionInput,
    MySearchLoginSessionsInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.login_session import LoginSessionAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2LoginSessionHandler:
    """REST v2 handler for login session operations."""

    def __init__(self, *, adapter: LoginSessionAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[AdminSearchLoginSessionsInput],
    ) -> APIResponse:
        """Search login sessions with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(
        self,
        body: BodyParam[MySearchLoginSessionsInput],
    ) -> APIResponse:
        """Search login sessions owned by the current user."""
        result = await self._adapter.my_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_revoke(
        self,
        body: BodyParam[AdminRevokeLoginSessionInput],
    ) -> APIResponse:
        """Revoke a login session (admin, no ownership check)."""
        result = await self._adapter.admin_revoke(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_revoke(
        self,
        body: BodyParam[MyRevokeLoginSessionInput],
    ) -> APIResponse:
        """Revoke a login session owned by the current user."""
        result = await self._adapter.my_revoke(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_unblock_user(
        self,
        body: BodyParam[AdminUnblockUserInput],
    ) -> APIResponse:
        """Clear the failed-login rate limit block for a user (admin only)."""
        result = await self._adapter.admin_unblock_user(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
