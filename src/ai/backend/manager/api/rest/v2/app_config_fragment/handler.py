"""REST v2 handler for the app config fragment domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config_fragment.adapter import (
        AppConfigFragmentAdapter,
    )

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigFragmentHandler:
    """REST v2 handler for admin-only app config fragment operations.

    App config fragments are managed by superadmins only; there are no user-facing endpoints.
    """

    _adapter: AppConfigFragmentAdapter

    def __init__(self, *, adapter: AppConfigFragmentAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[AdminSearchAppConfigFragmentInput],
    ) -> APIResponse:
        """Search fragments across all scopes with pagination (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
