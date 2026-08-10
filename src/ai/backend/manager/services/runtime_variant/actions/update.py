from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import RUNTIME_VARIANT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.runtime_variant.updaters import RuntimeVariantUpdater


@dataclass
class UpdateRuntimeVariantAction(UpdateGlobalOpsAction[RuntimeVariantRow, RuntimeVariantData]):
    """Rename a runtime variant or retouch its description."""

    updater: RuntimeVariantUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_runtime_variant"

    @override
    def to_updater(self) -> RuntimeVariantUpdater:
        return self.updater
