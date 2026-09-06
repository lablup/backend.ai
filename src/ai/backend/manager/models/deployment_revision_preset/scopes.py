"""Operation scopes for deployment revision presets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = ("DeploymentPresetSlotOperationScope",)


@dataclass(frozen=True)
class DeploymentPresetSlotOperationScope(OperationScope):
    """The slot amounts one preset declares."""

    preset_id: DeploymentPresetID

    @override
    def to_condition(self) -> QueryCondition:
        preset_id = self.preset_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PresetResourceSlotRow.preset_id == preset_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
