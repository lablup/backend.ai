"""The preset writes that carry over to the roles instantiated from the preset.

Each write and the sync of the derived roles share one transaction, so a preset never
commits ahead of the roles that stand for it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import FieldIdentifier
from ai.backend.manager.actions.v2.ops.result import BulkFieldOpsResult
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.rbac_models.role_permission_preset.creators import (
    RolePermissionPresetCreator,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.purgers import (
    RolePermissionPresetPurger,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.updaters import RolePresetUpdater
from ai.backend.manager.models.specs.purger import GuardedFieldPurger
from ai.backend.manager.repositories.ops.v2.role_preset.provider import RolePresetOpsProvider


class RolePresetRepository:
    _ops: RolePresetOpsProvider

    def __init__(self, ops_provider: RolePresetOpsProvider) -> None:
        self._ops = ops_provider

    async def update(self, updater: RolePresetUpdater) -> RolePresetData:
        """Apply the edit, then re-derive the preset's roles from it."""
        async with self._ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise EntityNotFoundError(f"RolePresetRow {updater.preset_id} not found")
            await w.sync_preset_roles(updater.preset_id)
            return data

    async def add_permissions(
        self, preset_id: RolePresetID, creators: Sequence[RolePermissionPresetCreator]
    ) -> list[RolePermissionPresetData]:
        """Insert the entries atomically, then widen the derived roles to them."""
        async with self._ops.write_ops() as w:
            items = await w.atomic_create_field_entities(preset_id, creators)
            await w.sync_preset_roles(preset_id)
            return items

    async def remove_permissions(
        self, purgers: Mapping[RolePermissionPresetID, RolePermissionPresetPurger]
    ) -> BulkFieldOpsResult[RolePermissionPresetData]:
        """Drop each named entry, then take the same permissions back from the roles of
        every preset an entry left."""
        named: Mapping[
            FieldIdentifier, GuardedFieldPurger[RolePermissionPresetRow, RolePermissionPresetData]
        ] = dict(purgers.items())
        async with self._ops.write_ops() as w:
            result = await w.partial_bulk_purge_field_entities(named)
            for preset_id in {entry.role_preset_id for entry in result.successes.values()}:
                await w.sync_preset_roles(preset_id)
            return result
