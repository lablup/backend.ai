from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.errors.resource import DeploymentRevisionPresetNotFound
from ai.backend.manager.models.deployment_revision_preset.creators import (
    PresetResourceSlotCreator,
)
from ai.backend.manager.models.deployment_revision_preset.purgers import (
    PresetResourceSlotBatchPurger,
)
from ai.backend.manager.models.deployment_revision_preset.queriers import (
    DeploymentPresetQuerier,
)
from ai.backend.manager.models.deployment_revision_preset.updaters import DeploymentPresetUpdater
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("DeploymentPresetRepository",)


class DeploymentPresetRepository:
    """The update that touches both tables, and the read internal callers hold no
    processor for. Everything keyed on one spec goes through ``OpsRepository``."""

    _ops: V2DBOpsProvider

    def __init__(self, v2_ops_provider: V2DBOpsProvider) -> None:
        self._ops = v2_ops_provider

    async def update(
        self,
        updater: DeploymentPresetUpdater,
        slot_creators: Sequence[PresetResourceSlotCreator] | None,
    ) -> DeploymentRevisionPresetData:
        """Apply the update and, when slots are given, restate the whole set.

        One transaction: a preset left with the old slots would ask for resources it no
        longer declares. ``None`` leaves the slots alone.
        """
        async with self._ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise DeploymentRevisionPresetNotFound(
                    f"Deployment preset with ID {updater.pk_value()} not found."
                )
            if slot_creators is not None:
                preset_id = data.entity_id()
                await w.batch_purge_in_global(PresetResourceSlotBatchPurger(preset_id))
                await w.atomic_create_field_entities(preset_id, slot_creators)
            return data

    async def get_by_id(self, preset_id: DeploymentPresetID) -> DeploymentRevisionPresetData:
        """Read one preset, for internal callers that hold no processor."""
        async with self._ops.read_ops() as r:
            data = await r.query_data(DeploymentPresetQuerier(preset_id=preset_id))
            if data is None:
                raise DeploymentRevisionPresetNotFound(
                    f"Deployment preset with ID {preset_id} not found."
                )
            return data
