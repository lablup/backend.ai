from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant.updaters import RuntimeVariantUpdater


@dataclass(frozen=True)
class PartialBulkUpdateRuntimeVariantsAction(
    UpdatePartialBulkOpsAction[RuntimeVariantRow, RuntimeVariantData]
):
    """Rename or retouch the named runtime variants, answering for each one."""

    updaters: Sequence[RuntimeVariantUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_runtime_variants"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.variant_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, RuntimeVariantUpdater]:
        return {updater.variant_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.variant_id in allowed]
        )
