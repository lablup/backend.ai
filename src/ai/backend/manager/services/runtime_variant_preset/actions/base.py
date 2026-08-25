from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant_preset import (
    RUNTIME_VARIANT_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class RuntimeVariantPresetGlobalAction(BaseGlobalAction):
    """Base for the preset operations the service still owns.

    Kept on the v2 global base even where the operation is not a pass-through: the
    gate and the audit shape belong to the shape, not to whether ops runs the write.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_PRESET_ENTITY_TYPE
