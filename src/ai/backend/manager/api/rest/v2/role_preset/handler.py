"""REST v2 handler for the role preset domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkRemoveRolePermissionPresetsInput,
    SearchRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkDeleteRolePresetsInput,
    BulkPurgeRolePresetsInput,
    BulkRestoreRolePresetsInput,
    CreateRolePresetInput,
    SearchRolePresetsInput,
    UpdateRolePresetBody,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import RolePresetIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2RolePresetHandler:
    """REST v2 handler for role preset operations.

    Delete is a soft-delete (toggles ``deleted = true``); Restore inverts it;
    Purge performs the hard delete and cascades to permission entries.
    """

    def __init__(self, *, adapter: RolePresetAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateRolePresetInput],
    ) -> APIResponse:
        """Create a new role preset."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search(
        self,
        body: BodyParam[SearchRolePresetsInput],
    ) -> APIResponse:
        """Search role presets (superadmin only)."""
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[RolePresetIdPathParam],
    ) -> APIResponse:
        """Get a single role preset by ID."""
        result = await self._adapter.get(path.parsed.role_preset_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[RolePresetIdPathParam],
        body: BodyParam[UpdateRolePresetBody],
    ) -> APIResponse:
        """Update a role preset's metadata. The ``deleted`` flag cannot be mutated here.

        The preset ID comes from the URL path; the adapter merges it with the body.
        """
        result = await self._adapter.update_from_body(path.parsed.role_preset_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_delete(
        self,
        body: BodyParam[BulkDeleteRolePresetsInput],
    ) -> APIResponse:
        """Soft-delete role presets (sets ``deleted = true``)."""
        result = await self._adapter.bulk_delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_restore(
        self,
        body: BodyParam[BulkRestoreRolePresetsInput],
    ) -> APIResponse:
        """Restore soft-deleted role presets (sets ``deleted = false``)."""
        result = await self._adapter.bulk_restore(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def bulk_purge(
        self,
        body: BodyParam[BulkPurgeRolePresetsInput],
    ) -> APIResponse:
        """Hard-delete role presets, cascading to their permission entries."""
        result = await self._adapter.bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_permissions(
        self,
        path: PathParam[RolePresetIdPathParam],
        body: BodyParam[SearchRolePermissionPresetsInput],
    ) -> APIResponse:
        """Search the permission entries belonging to a single role preset."""
        result = await self._adapter.search_permission_presets(
            path.parsed.role_preset_id,
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def add_permissions(
        self,
        path: PathParam[RolePresetIdPathParam],
        body: BodyParam[BulkAddRolePermissionPresetsInput],
    ) -> APIResponse:
        """Bulk-add permission entries to an existing role preset."""
        result = await self._adapter.bulk_add_permissions(
            path.parsed.role_preset_id,
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def remove_permissions(
        self,
        body: BodyParam[BulkRemoveRolePermissionPresetsInput],
    ) -> APIResponse:
        """Bulk-remove permission entries by their row IDs."""
        result = await self._adapter.bulk_remove_permissions(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
