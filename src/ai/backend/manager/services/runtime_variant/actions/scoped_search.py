"""Runtime variant search over the scopes a variant is reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow

__all__ = ("ScopedSearchRuntimeVariantsAction",)


@dataclass(frozen=True)
class ScopedSearchRuntimeVariantsAction(
    ScopedSearchOpsAction[RuntimeVariantRow, RuntimeVariantData]
):
    """Page through the runtime variants the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the
    rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RuntimeVariantEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_runtime_variants"
