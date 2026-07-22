"""REST v2 handler for the app config fragment domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    BulkPurgeAppConfigFragmentInput,
    BulkUpdateAppConfigFragmentInput,
    CreateAppConfigFragmentInput,
    ScopedSearchAppConfigFragmentInput,
    UpdateAppConfigFragmentInput,
)
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import AppConfigFragmentIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config_fragment.adapter import (
        AppConfigFragmentAdapter,
    )

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigFragmentHandler:
    """REST v2 handler for raw app config fragment operations."""

    _adapter: AppConfigFragmentAdapter

    def __init__(self, *, adapter: AppConfigFragmentAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateAppConfigFragmentInput],
    ) -> APIResponse:
        """Create a fragment at the caller's authorized scope (auth required, RBAC-gated)."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(
        self,
        path: PathParam[AppConfigFragmentIdPathParam],
    ) -> APIResponse:
        """Get a fragment by id (auth required, RBAC-gated)."""
        result = await self._adapter.get(AppConfigFragmentID(path.parsed.fragment_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[AppConfigFragmentIdPathParam],
        body: BodyParam[UpdateAppConfigFragmentInput],
    ) -> APIResponse:
        """Update a fragment's config document by id (auth required, RBAC-gated)."""
        result = await self._adapter.update(
            AppConfigFragmentID(path.parsed.fragment_id), body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[AppConfigFragmentIdPathParam],
    ) -> APIResponse:
        """Purge a fragment by id (auth required, RBAC-gated)."""
        result = await self._adapter.purge(AppConfigFragmentID(path.parsed.fragment_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_update(
        self,
        body: BodyParam[BulkUpdateAppConfigFragmentInput],
    ) -> APIResponse:
        """Update many fragments' configs by id, with per-item partial success (auth, RBAC)."""
        result = await self._adapter.bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_purge(
        self,
        body: BodyParam[BulkPurgeAppConfigFragmentInput],
    ) -> APIResponse:
        """Purge many fragments by id, with per-item partial success (auth, RBAC)."""
        result = await self._adapter.bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[AdminSearchAppConfigFragmentInput],
    ) -> APIResponse:
        """Search fragments across all scopes with pagination (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search(
        self,
        body: BodyParam[ScopedSearchAppConfigFragmentInput],
    ) -> APIResponse:
        """Search the fragments written at one domain / user scope (auth required)."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
