"""REST v2 handler for the system session environ domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.system_session_environ.adapter import (
        SystemSessionEnvironAdapter,
    )


class V2SystemSessionEnvironHandler:
    """REST v2 handler for the system session environ domain."""

    _adapter: SystemSessionEnvironAdapter

    def __init__(self, *, adapter: SystemSessionEnvironAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[AdminSearchSystemSessionEnvironsInput],
    ) -> APIResponse:
        """Search every system session environ row, at every scope (superadmin only)."""
        payload = await self._adapter.global_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def list_value_sources(self) -> APIResponse:
        """List every value source a system session environ row can carry."""
        payload = await self._adapter.public_list_value_sources()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
