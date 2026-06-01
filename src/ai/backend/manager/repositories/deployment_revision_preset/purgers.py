from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec


@dataclass
class PresetResourceSlotBatchPurgerSpec(BatchPurgerSpec[PresetResourceSlotRow]):
    """Selects all resource slot rows belonging to a single preset for deletion."""

    preset_id: uuid.UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[PresetResourceSlotRow]]:
        return sa.select(PresetResourceSlotRow).where(
            PresetResourceSlotRow.preset_id == self.preset_id
        )
