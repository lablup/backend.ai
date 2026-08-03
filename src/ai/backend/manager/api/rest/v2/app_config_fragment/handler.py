"""REST v2 handler for the app config fragment domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    BulkPurgeAppConfigFragmentInput,
    MyAppConfigFragmentsByNamesInput,
    MyPurgeAppConfigFragmentsByNamesInput,
    MyUpsertAppConfigFragmentsInput,
    ScopedAppConfigFragmentsByNamesInput,
    ScopedUpsertAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentsByNamesPayload,
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

    async def get(
        self,
        path: PathParam[AppConfigFragmentIdPathParam],
    ) -> APIResponse:
        """Get a fragment by id (auth required, RBAC-gated)."""
        result = await self._adapter.get(AppConfigFragmentID(path.parsed.fragment_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[AppConfigFragmentIdPathParam],
    ) -> APIResponse:
        """Purge a fragment by id (auth required, RBAC-gated)."""
        result = await self._adapter.purge(AppConfigFragmentID(path.parsed.fragment_id))
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

    async def scoped_fragments_by_names(
        self,
        body: BodyParam[ScopedAppConfigFragmentsByNamesInput],
    ) -> APIResponse:
        """Read one scope's fragments for the given config names (auth, RBAC-authorized)."""
        nodes = await self._adapter.scoped_app_config_fragments_by_names(body.parsed)
        return APIResponse.build(
            status_code=HTTPStatus.OK, response_model=AppConfigFragmentsByNamesPayload(nodes)
        )

    async def my_fragments_by_names(
        self,
        body: BodyParam[MyAppConfigFragmentsByNamesInput],
    ) -> APIResponse:
        """Read the caller's own user-scope fragments for the given config names (auth)."""
        nodes = await self._adapter.my_app_config_fragments_by_names(body.parsed)
        return APIResponse.build(
            status_code=HTTPStatus.OK, response_model=AppConfigFragmentsByNamesPayload(nodes)
        )

    async def scoped_bulk_upsert(
        self,
        body: BodyParam[ScopedUpsertAppConfigFragmentsInput],
    ) -> APIResponse:
        """Upsert many fragments at one scope, all-or-nothing (auth, RBAC-authorized)."""
        result = await self._adapter.scoped_upsert_app_config_fragments(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_bulk_upsert(
        self,
        body: BodyParam[MyUpsertAppConfigFragmentsInput],
    ) -> APIResponse:
        """Upsert many fragments at the caller's own user scope, all-or-nothing (auth)."""
        result = await self._adapter.my_upsert_app_config_fragments(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_bulk_purge(
        self,
        body: BodyParam[MyPurgeAppConfigFragmentsByNamesInput],
    ) -> APIResponse:
        """Purge the caller's own user-scope fragments by config name, all-or-nothing (auth)."""
        result = await self._adapter.my_purge_app_config_fragments_by_names(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
