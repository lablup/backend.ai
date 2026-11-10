"""REST v2 handler for the session lifecycle handler registry."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.session_lifecycle_handler.adapter import (
        SessionLifecycleHandlerAdapter,
    )


class V2SessionLifecycleHandlerHandler:
    """REST v2 handler exposing the session lifecycle handler registry."""

    _adapter: SessionLifecycleHandlerAdapter

    def __init__(self, *, adapter: SessionLifecycleHandlerAdapter) -> None:
        self._adapter = adapter

    async def admin_list(self) -> APIResponse:
        """List all registered session lifecycle handlers (superadmin only)."""
        payload = await self._adapter.list_session_lifecycle_handlers()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
