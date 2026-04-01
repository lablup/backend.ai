"""REST v2 handler for the login history domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.login_history.request import (
    AdminSearchLoginHistoryInput,
    MySearchLoginHistoryInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.login_history import LoginHistoryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2LoginHistoryHandler:
    """REST v2 handler for login history operations."""

    def __init__(self, *, adapter: LoginHistoryAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[AdminSearchLoginHistoryInput],
    ) -> APIResponse:
        """Search login history with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(
        self,
        body: BodyParam[MySearchLoginHistoryInput],
    ) -> APIResponse:
        """Search login history of the current user."""
        result = await self._adapter.my_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
