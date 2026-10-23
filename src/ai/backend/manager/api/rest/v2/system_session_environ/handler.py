"""REST v2 handler for the system session environ domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminResolveSystemSessionEnvironInput,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.system_session_environ.adapter import (
        SystemSessionEnvironAdapter,
    )


class V2SystemSessionEnvironHandler:
    """REST v2 handler for the system session environ domain."""

    def __init__(self, *, adapter: SystemSessionEnvironAdapter) -> None:
        self._adapter = adapter

    async def admin_resolve(
        self,
        body: BodyParam[AdminResolveSystemSessionEnvironInput],
    ) -> APIResponse:
        """Read the rows a session in the domain and project receives (superadmin only)."""
        payload = await self._adapter.global_resolve(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
