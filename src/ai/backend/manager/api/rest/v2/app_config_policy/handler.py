"""REST v2 handler for the app-config policy domain.

Writes are **bulk-only** — the single-item create / update / purge
endpoints were removed in favour of `/bulk-create`, `/bulk-update`,
`/bulk-purge` (admin-only).
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminBulkCreateAppConfigPoliciesInput,
    AdminBulkPurgeAppConfigPoliciesInput,
    AdminBulkUpdateAppConfigPoliciesInput,
    AdminSearchAppConfigPoliciesInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import AppConfigPolicyIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config_policy import AppConfigPolicyAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigPolicyHandler:
    """REST v2 handler for app-config policy operations."""

    def __init__(self, *, adapter: AppConfigPolicyAdapter) -> None:
        self._adapter = adapter

    # ── Reads ────────────────────────────────────────────────────

    async def get(
        self,
        path: PathParam[AppConfigPolicyIdPathParam],
    ) -> APIResponse:
        """Read a single policy by row id (any authenticated user)."""
        result = await self._adapter.get(path.parsed.policy_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[AdminSearchAppConfigPoliciesInput],
    ) -> APIResponse:
        """Paginated system-wide policy search (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ── Admin bulk writes ────────────────────────────────────────

    async def admin_bulk_create(
        self,
        body: BodyParam[AdminBulkCreateAppConfigPoliciesInput],
    ) -> APIResponse:
        """Strict insert; per-item transactions (admin only)."""
        result = await self._adapter.admin_bulk_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_bulk_update(
        self,
        body: BodyParam[AdminBulkUpdateAppConfigPoliciesInput],
    ) -> APIResponse:
        """Replace `scope_sources` (admin only). `config_name` is immutable."""
        result = await self._adapter.admin_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_bulk_purge(
        self,
        body: BodyParam[AdminBulkPurgeAppConfigPoliciesInput],
    ) -> APIResponse:
        """Hard-delete by row id (admin only); rows still referenced by fragments fail per-item."""
        result = await self._adapter.admin_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
