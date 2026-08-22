from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import RUNTIME_VARIANT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.creators import RuntimeVariantCreator
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow


@dataclass
class CreateRuntimeVariantAction(CreateGlobalOpsAction[RuntimeVariantRow, RuntimeVariantData]):
    """Register a runtime variant in the global catalog."""

    creator: RuntimeVariantCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_runtime_variant"

    @override
    def to_creator(self) -> RuntimeVariantCreator:
        return self.creator
