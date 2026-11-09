from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction
from ai.backend.manager.models.runtime_variant_preset.updaters import RuntimeVariantPresetUpdater


@dataclass(frozen=True)
class PartialBulkUpdateRuntimeVariantPresetsAction(BasePartialBulkAction):
    """Change the named presets, answering for each one.

    Service-kept for the same check the single update runs against the stored row.
    """

    updaters: Sequence[RuntimeVariantPresetUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_runtime_variant_presets"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.preset_id for updater in self.updaters)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.preset_id in allowed]
        )
