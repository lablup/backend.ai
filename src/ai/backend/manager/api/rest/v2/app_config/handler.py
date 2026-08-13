"""REST v2 handler for the merged app config (read) domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigHandler:
    """REST v2 handler for the merged AppConfig read operations."""

    _adapter: AppConfigAdapter

    def __init__(self, *, adapter: AppConfigAdapter) -> None:
        self._adapter = adapter

    async def my_get_app_configs(
        self,
        body: BodyParam[MyGetAppConfigsInput],
    ) -> APIResponse:
        """Get the acting user's merged AppConfigs (auth required)."""
        result = await self._adapter.my_get_app_configs(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def public_get_app_configs(
        self,
        body: BodyParam[PublicGetAppConfigsInput],
    ) -> APIResponse:
        """Get merged AppConfigs from public fragments only (anonymous)."""
        result = await self._adapter.public_get_app_configs(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
