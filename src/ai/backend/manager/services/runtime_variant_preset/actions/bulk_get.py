from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.queriers import (
    BulkRuntimeVariantPresetQuerier,
)
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow


@dataclass
class BulkGetRuntimeVariantPresetsAction(
    PartialBulkGetEntityOpsAction[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Read the runtime variant presets the caller named, one permission check per preset."""

    ids: Sequence[RuntimeVariantPresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_runtime_variant_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkRuntimeVariantPresetQuerier:
        return BulkRuntimeVariantPresetQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
