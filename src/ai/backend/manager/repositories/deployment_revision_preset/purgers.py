from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec, PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class PresetResourceSlotBatchPurgerSpec(BatchPurgerSpec[PresetResourceSlotRow]):
    """Selects all resource slot rows belonging to a single preset for deletion."""

    preset_id: uuid.UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[PresetResourceSlotRow]]:
        return sa.select(PresetResourceSlotRow).where(
            PresetResourceSlotRow.preset_id == self.preset_id
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class DeploymentRevisionPresetPurgerSpec(PurgerSpec[DeploymentRevisionPresetRow]):
    """PurgerSpec for deleting a deployment revision preset."""

    preset_id: uuid.UUID

    @override
    def row_class(self) -> type[DeploymentRevisionPresetRow]:
        return DeploymentRevisionPresetRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
