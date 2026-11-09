from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction
from ai.backend.manager.services.deployment_revision_preset.actions.update import (
    UpdateDeploymentPresetAction,
)


@dataclass
class PartialBulkUpdateDeploymentPresetsAction(BasePartialBulkAction):
    """Retune the named presets, answering for each one."""

    updates: Sequence[UpdateDeploymentPresetAction]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_deployment_presets"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(update.preset_id for update in self.updates)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updates=[update for update in self.updates if update.preset_id in allowed]
        )
