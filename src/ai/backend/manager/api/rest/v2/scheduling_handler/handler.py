"""REST v2 handler for the scheduling-handler registry domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.scheduling_handler.adapter import SchedulingHandlerAdapter


class V2SchedulingHandlerHandler:
    """REST v2 handler exposing the deployment scheduling handler registry."""

    def __init__(self, *, adapter: SchedulingHandlerAdapter) -> None:
        self._adapter = adapter

    async def admin_list(self) -> APIResponse:
        """List all registered deployment scheduling handlers (admin only)."""
        payload = await self._adapter.list_scheduling_handlers()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
