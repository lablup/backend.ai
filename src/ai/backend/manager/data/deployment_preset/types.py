from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.types import FieldData


@dataclass(frozen=True)
class PresetResourceSlotData(FieldData):
    """One slot's amount on the preset that owns it.

    Its own type rather than the shared slot entry: a field row answers with the entity
    owning it, and the shared entry is written for deployment revisions too.
    """

    preset_id: DeploymentPresetID
    slot_name: str
    quantity: Decimal
