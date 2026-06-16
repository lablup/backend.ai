"""REST v2 handler for the app-config fragment domain.

Writes are **bulk-only** per BEP §3 — the single-item create / update /
purge endpoints were removed in favour of `/bulk-create`,
`/bulk-update`, `/bulk-purge` (admin) and `/my/bulk-create`,
`/my/bulk-update` (self-service).
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminBulkCreateAppConfigFragmentsInput,
    AdminBulkPurgeAppConfigFragmentsInput,
    AdminBulkUpdateAppConfigFragmentsInput,
    AppConfigFragmentKeyInput,
    MyBulkCreateAppConfigFragmentsInput,
    MyBulkUpdateAppConfigFragmentsInput,
    SearchAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import AppConfigFragmentScopePathParam
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigScopeType as DataAppConfigScopeType,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config import AppConfigAdapter
    from ai.backend.manager.api.adapters.app_config_fragment import AppConfigFragmentAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigFragmentHandler:
    """REST v2 handler for app-config fragment operations.

    Self-service `my_bulk_*` writes return recomputed merged
    `AppConfig` views, so they are dispatched to `AppConfigAdapter`;
    everything else is the raw-row Fragment surface.
    """

    def __init__(
        self,
        *,
        adapter: AppConfigFragmentAdapter,
        app_config_adapter: AppConfigAdapter,
    ) -> None:
        self._adapter = adapter
        self._app_config_adapter = app_config_adapter

    # ── Reads ────────────────────────────────────────────────────

    async def get(
        self,
        body: BodyParam[AppConfigFragmentKeyInput],
    ) -> APIResponse:
        """Read a single fragment by natural key (any authenticated user)."""
        result = await self._adapter.get(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search(
        self,
        path: PathParam[AppConfigFragmentScopePathParam],
        body: BodyParam[SearchAppConfigFragmentsInput],
    ) -> APIResponse:
        """Scope-bound fragment search — caller is pinned to a specific
        `(scope_type, scope_id)` pair via the URL path.
        """
        result = await self._adapter.search(
            scope_type=DataAppConfigScopeType(path.parsed.scope_type),
            scope_id=path.parsed.scope_id,
            input=body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchAppConfigFragmentsInput],
    ) -> APIResponse:
        """Cross-scope admin search (admin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ── Admin bulk writes ──────────────────────────

    async def admin_bulk_create(
        self,
        body: BodyParam[AdminBulkCreateAppConfigFragmentsInput],
    ) -> APIResponse:
        """Strict insert across any scope; per-item transactions (admin only)."""
        result = await self._adapter.admin_bulk_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_bulk_update(
        self,
        body: BodyParam[AdminBulkUpdateAppConfigFragmentsInput],
    ) -> APIResponse:
        """Wholesale JSON replacement; per-item transactions (admin only)."""
        result = await self._adapter.admin_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_bulk_purge(
        self,
        body: BodyParam[AdminBulkPurgeAppConfigFragmentsInput],
    ) -> APIResponse:
        """Cleanup-only deletion; absent keys are no-oped (admin only)."""
        result = await self._adapter.admin_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ── Self-service bulk writes ───────────────────

    async def my_bulk_create(
        self,
        body: BodyParam[MyBulkCreateAppConfigFragmentsInput],
    ) -> APIResponse:
        """Self-service bulk create on the caller's `USER` row."""
        result = await self._app_config_adapter.my_bulk_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_bulk_update(
        self,
        body: BodyParam[MyBulkUpdateAppConfigFragmentsInput],
    ) -> APIResponse:
        """Self-service bulk update on the caller's `USER` row."""
        result = await self._app_config_adapter.my_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)


# ``AppConfigScopeType`` is imported for OpenAPI schema visibility of the
# string-form path parameter; keep the import alive.
_ = AppConfigScopeType
