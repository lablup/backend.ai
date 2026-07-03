"""REST v2 handler for the app config allow-list domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    CreateAppConfigAllowListInput,
    PurgeAppConfigAllowListInput,
    SearchAppConfigAllowListInput,
    UpdateAppConfigAllowListInput,
)
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import AppConfigAllowListIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
        AppConfigAllowListAdapter,
    )

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigAllowListHandler:
    """REST v2 handler for app config allow-list operations (admin-only)."""

    def __init__(self, *, adapter: AppConfigAllowListAdapter) -> None:
        self._adapter = adapter

    async def admin_create(
        self,
        body: BodyParam[CreateAppConfigAllowListInput],
    ) -> APIResponse:
        """Register a new app config allow-list entry (superadmin only)."""
        result = await self._adapter.admin_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchAppConfigAllowListInput],
    ) -> APIResponse:
        """Search app config allow-list entries with pagination (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_get(
        self,
        path: PathParam[AppConfigAllowListIdPathParam],
    ) -> APIResponse:
        """Get an app config allow-list entry by id (superadmin only)."""
        result = await self._adapter.admin_get(
            AppConfigAllowListID(path.parsed.app_config_allow_list_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update(
        self,
        path: PathParam[AppConfigAllowListIdPathParam],
        body: BodyParam[UpdateAppConfigAllowListInput],
    ) -> APIResponse:
        """Update an app config allow-list entry's rank by id (superadmin only)."""
        merged = body.parsed.model_copy(update={"id": path.parsed.app_config_allow_list_id})
        result = await self._adapter.admin_update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        path: PathParam[AppConfigAllowListIdPathParam],
    ) -> APIResponse:
        """Purge an app config allow-list entry by id (superadmin only)."""
        result = await self._adapter.admin_purge(
            PurgeAppConfigAllowListInput(id=path.parsed.app_config_allow_list_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
