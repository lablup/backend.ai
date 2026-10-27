"""REST v2 handler for the system session environ domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.system_session_environ.adapter import (
        SystemSessionEnvironAdapter,
    )


class V2SystemSessionEnvironHandler:
    """REST v2 handler for the system session environ domain."""

    _adapter: SystemSessionEnvironAdapter

    def __init__(self, *, adapter: SystemSessionEnvironAdapter) -> None:
        self._adapter = adapter

    async def list_value_sources(self) -> APIResponse:
        """List every value source a system session environ row can carry."""
        payload = await self._adapter.public_list_value_sources()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
