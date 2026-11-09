"""REST v2 handler for the app config allow-list domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    CreateAppConfigAllowListInput,
    PartialBulkPurgeAppConfigAllowListsInput,
    PartialBulkUpdateAppConfigAllowListsInput,
    PurgeAppConfigAllowListInput,
    SearchAppConfigAllowListInput,
    UpdateAppConfigAllowListInput,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import AppConfigAllowListIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
        AppConfigAllowListAdapter,
    )

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


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

    async def update(
        self,
        path: PathParam[AppConfigAllowListIdPathParam],
        body: BodyParam[UpdateAppConfigAllowListInput],
    ) -> APIResponse:
        """Update an app config allow-list entry's rank by id."""
        merged = body.parsed.model_copy(update={"id": path.parsed.app_config_allow_list_id})
        result = await self._adapter.update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[AppConfigAllowListIdPathParam],
    ) -> APIResponse:
        """Purge an app config allow-list entry by id, with the fragments it admits."""
        result = await self._adapter.purge(
            PurgeAppConfigAllowListInput(id=path.parsed.app_config_allow_list_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update(
        self,
        body: BodyParam[PartialBulkUpdateAppConfigAllowListsInput],
    ) -> APIResponse:
        """Update several app config allow-list entries, answering for each one."""
        result = await self._adapter.partial_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge(
        self,
        body: BodyParam[PartialBulkPurgeAppConfigAllowListsInput],
    ) -> APIResponse:
        """Purge several app config allow-list entries, answering for each one."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update(
        self,
        path: PathParam[AppConfigAllowListIdPathParam],
        body: BodyParam[UpdateAppConfigAllowListInput],
    ) -> APIResponse:
        """Deprecated. Use `PATCH /v2/app-config-allow-lists/{app_config_allow_list_id}`."""
        merged = body.parsed.model_copy(update={"id": path.parsed.app_config_allow_list_id})
        result = await self._adapter.update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        path: PathParam[AppConfigAllowListIdPathParam],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/app-config-allow-lists/{app_config_allow_list_id}`."""
        result = await self._adapter.purge(
            PurgeAppConfigAllowListInput(id=path.parsed.app_config_allow_list_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
