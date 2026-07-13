"""REST v2 handler for the app config fragment domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    CreateAppConfigFragmentInput,
    PurgeAppConfigFragmentInput,
    ScopedSearchAppConfigFragmentInput,
    SearchAppConfigFragmentInput,
    UpdateAppConfigFragmentInput,
)
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import AppConfigFragmentIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigFragmentHandler:
    """REST v2 handler for raw app config fragment operations."""

    def __init__(self, *, adapter: AppConfigAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateAppConfigFragmentInput],
    ) -> APIResponse:
        """Create a fragment; authorized by the layer's permission policy (auth required)."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_get(
        self,
        path: PathParam[AppConfigFragmentIdPathParam],
    ) -> APIResponse:
        """Get a fragment by id (superadmin only)."""
        result = await self._adapter.admin_get(AppConfigFragmentID(path.parsed.fragment_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[AppConfigFragmentIdPathParam],
        body: BodyParam[UpdateAppConfigFragmentInput],
    ) -> APIResponse:
        """Update a fragment's config; authorized by the layer's permission policy (auth required)."""
        result = await self._adapter.update(
            AppConfigFragmentID(path.parsed.fragment_id), body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[AppConfigFragmentIdPathParam],
    ) -> APIResponse:
        """Purge a fragment by id; authorized by the layer's permission policy (auth required)."""
        result = await self._adapter.purge(PurgeAppConfigFragmentInput(id=path.parsed.fragment_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchAppConfigFragmentInput],
    ) -> APIResponse:
        """Search fragments across all scopes with pagination (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search(
        self,
        body: BodyParam[ScopedSearchAppConfigFragmentInput],
    ) -> APIResponse:
        """Search the fragments visible to the calling principal (auth required)."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
