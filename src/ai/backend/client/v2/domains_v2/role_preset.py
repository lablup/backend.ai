"""V2 SDK client for the role preset domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkRemoveRolePermissionPresetsInput,
    SearchRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkAddRolePermissionPresetsPayload,
    BulkRemoveRolePermissionPresetsPayload,
    SearchRolePermissionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkDeleteRolePresetsInput,
    BulkPurgeRolePresetsInput,
    BulkRestoreRolePresetsInput,
    CreateRolePresetInput,
    SearchRolePresetsInput,
    UpdateRolePresetBody,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkDeleteRolePresetsPayload,
    BulkPurgeRolePresetsPayload,
    BulkRestoreRolePresetsPayload,
    CreateRolePresetPayload,
    RolePresetNode,
    SearchRolePresetsPayload,
    UpdateRolePresetPayload,
)
from ai.backend.common.identifier.role_preset import RolePresetID

_PATH = "/v2/role-presets"


class V2RolePresetClient(BaseDomainClient):
    """SDK client for ``/v2/role-presets`` endpoints (superadmin only).

    Delete is a soft-delete; Restore inverts it; Purge is the hard delete.
    Every active preset is auto-applied at scope creation, so there is no
    ``auto_apply`` argument on this surface.
    """

    async def create(self, request: CreateRolePresetInput) -> CreateRolePresetPayload:
        """Create a new role preset."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateRolePresetPayload,
        )

    async def get(self, role_preset_id: RolePresetID) -> RolePresetNode:
        """Get a single role preset by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{role_preset_id}",
            response_model=RolePresetNode,
        )

    async def search(self, request: SearchRolePresetsInput) -> SearchRolePresetsPayload:
        """Search role presets across the system."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchRolePresetsPayload,
        )

    async def update(
        self, role_preset_id: RolePresetID, request: UpdateRolePresetBody
    ) -> UpdateRolePresetPayload:
        """Update a role preset's mutable metadata."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{role_preset_id}",
            request=request,
            response_model=UpdateRolePresetPayload,
        )

    async def delete(self, request: BulkDeleteRolePresetsInput) -> BulkDeleteRolePresetsPayload:
        """Soft-delete role presets (sets ``deleted = true``)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-delete",
            request=request,
            response_model=BulkDeleteRolePresetsPayload,
        )

    async def restore(self, request: BulkRestoreRolePresetsInput) -> BulkRestoreRolePresetsPayload:
        """Restore soft-deleted role presets (sets ``deleted = false``)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-restore",
            request=request,
            response_model=BulkRestoreRolePresetsPayload,
        )

    async def purge(self, request: BulkPurgeRolePresetsInput) -> BulkPurgeRolePresetsPayload:
        """Hard-delete role presets, cascading to their permission entries."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-purge",
            request=request,
            response_model=BulkPurgeRolePresetsPayload,
        )

    async def search_permissions(
        self, role_preset_id: RolePresetID, request: SearchRolePermissionPresetsInput
    ) -> SearchRolePermissionPresetsPayload:
        """Search the permission entries belonging to a single role preset."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{role_preset_id}/permissions/search",
            request=request,
            response_model=SearchRolePermissionPresetsPayload,
        )

    async def add_permissions(
        self, role_preset_id: RolePresetID, request: BulkAddRolePermissionPresetsInput
    ) -> BulkAddRolePermissionPresetsPayload:
        """Bulk-add permission entries to an existing role preset."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{role_preset_id}/permissions/add",
            request=request,
            response_model=BulkAddRolePermissionPresetsPayload,
        )

    async def remove_permissions(
        self, request: BulkRemoveRolePermissionPresetsInput
    ) -> BulkRemoveRolePermissionPresetsPayload:
        """Bulk-remove permission entries by their row IDs."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/permissions/remove",
            request=request,
            response_model=BulkRemoveRolePermissionPresetsPayload,
        )
