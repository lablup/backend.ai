"""REST v2 handler for the app config definition domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    CreateAppConfigDefinitionInput,
    PurgeAppConfigDefinitionInput,
    SearchAppConfigDefinitionsInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import AppConfigDefinitionIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config_definition.adapter import (
        AppConfigDefinitionAdapter,
    )

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigDefinitionHandler:
    """REST v2 handler for app config definition operations (admin-only)."""

    def __init__(self, *, adapter: AppConfigDefinitionAdapter) -> None:
        self._adapter = adapter

    async def admin_create(
        self,
        body: BodyParam[CreateAppConfigDefinitionInput],
    ) -> APIResponse:
        """Register a new app config definition (superadmin only)."""
        result = await self._adapter.admin_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchAppConfigDefinitionsInput],
    ) -> APIResponse:
        """Search app config definitions with pagination (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_get(
        self,
        path: PathParam[AppConfigDefinitionIdPathParam],
    ) -> APIResponse:
        """Get an app config definition by id (superadmin only)."""
        result = await self._adapter.admin_get(path.parsed.app_config_definition_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        path: PathParam[AppConfigDefinitionIdPathParam],
    ) -> APIResponse:
        """Purge an app config definition by id (superadmin only)."""
        result = await self._adapter.admin_purge(
            PurgeAppConfigDefinitionInput(id=path.parsed.app_config_definition_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
