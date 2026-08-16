from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant_preset import (
    RUNTIME_VARIANT_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.runtime_variant_preset.queriers import (
    RuntimeVariantPresetQuerier,
)


@dataclass
class GetRuntimeVariantPresetAction(
    GetSingleEntityOpsAction[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Read one runtime variant preset; every authenticated user may."""

    preset_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_get_runtime_variant_preset"

    @override
    def entity_id(self) -> EntityID:
        return self.preset_id

    @override
    def to_querier(self) -> RuntimeVariantPresetQuerier:
        return RuntimeVariantPresetQuerier(preset_id=self.preset_id)
