"""Read specs for a deployment preset's slot rows."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment_preset import (
    DEPLOYMENT_PRESET_ENTITY_TYPE,
    DeploymentPresetID,
)
from ai.backend.common.data.entity.preset_resource_slot import PresetResourceSlotID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup

__all__ = ("PresetResourceSlotOwnerLookup",)


class PresetResourceSlotOwnerLookup(FieldOwnerLookup[PresetResourceSlotID, DeploymentPresetID]):
    """The preset a slot row belongs to."""

    @override
    def build_query(self, field_ids: Sequence[PresetResourceSlotID]) -> sa.sql.Select[Any]:
        return sa.select(
            PresetResourceSlotRow.id,
            PresetResourceSlotRow.preset_id,
            sa.literal(DEPLOYMENT_PRESET_ENTITY_TYPE),
        ).where(PresetResourceSlotRow.id.in_(field_ids))

    @override
    def to_entity_id(self, value: UUID, owner_type: EntityType) -> DeploymentPresetID:
        return DeploymentPresetID(value)
