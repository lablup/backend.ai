"""Role preset domain adapter - Pydantic-in/Pydantic-out transport layer.

Shared between the GraphQL resolvers and REST v2 handlers. Method bodies raise
``NotImplementedError``; wire-up to the Processor/Service layer happens in a
follow-up task.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkRemoveRolePermissionPresetsInput,
    RolePermissionPresetFilter,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkAddRolePermissionPresetsPayload,
    BulkRemoveRolePermissionPresetsPayload,
    RolePermissionPresetNode,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkPurgeRolePresetsInput,
    CreateRolePresetInput,
    SearchRolePresetsInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkPurgeRolePresetsPayload,
    CreateRolePresetPayload,
    RolePresetNode,
    SearchRolePresetsPayload,
)
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.api.adapters.base import BaseAdapter


class RolePresetAdapter(BaseAdapter):
    """Adapter for role preset domain operations."""

    async def create(self, input: CreateRolePresetInput) -> CreateRolePresetPayload:
        """Create a new role preset."""
        raise NotImplementedError

    async def get(self, role_preset_id: RolePresetID) -> RolePresetNode | None:
        """Get a single role preset by ID."""
        raise NotImplementedError

    async def search(self, input: SearchRolePresetsInput) -> SearchRolePresetsPayload:
        """Search role presets with filtering and pagination."""
        raise NotImplementedError

    async def bulk_purge(self, input: BulkPurgeRolePresetsInput) -> BulkPurgeRolePresetsPayload:
        """Bulk-hard-delete role presets."""
        raise NotImplementedError

    async def search_permissions(
        self, input: RolePermissionPresetFilter
    ) -> list[RolePermissionPresetNode]:
        """Resolve the permission entries belonging to a role preset.

        Backs the ``permission_presets`` field resolver on ``RolePresetNode``; the caller
        supplies ``role_preset_id`` via the filter.
        """
        raise NotImplementedError

    async def bulk_add_permissions(
        self,
        role_preset_id: RolePresetID,
        input: BulkAddRolePermissionPresetsInput,
    ) -> BulkAddRolePermissionPresetsPayload:
        """Bulk-add permission entries to an existing role preset."""
        raise NotImplementedError

    async def bulk_remove_permissions(
        self, input: BulkRemoveRolePermissionPresetsInput
    ) -> BulkRemoveRolePermissionPresetsPayload:
        """Bulk-remove permission entries from a role preset."""
        raise NotImplementedError
