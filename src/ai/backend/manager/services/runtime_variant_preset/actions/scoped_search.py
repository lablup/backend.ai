"""Runtime variant preset search over the scopes a preset is reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant_preset import (
    RuntimeVariantPresetEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow

__all__ = ("ScopedSearchRuntimeVariantPresetsAction",)


@dataclass(frozen=True)
class ScopedSearchRuntimeVariantPresetsAction(
    ScopedSearchOpsAction[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Page through the runtime variant presets the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the
    rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RuntimeVariantPresetEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_runtime_variant_presets"
