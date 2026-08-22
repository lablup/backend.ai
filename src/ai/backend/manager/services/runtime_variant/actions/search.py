from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import RUNTIME_VARIANT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant.searchers import RuntimeVariantSearcher


@dataclass
class SearchRuntimeVariantsAction(SearchGlobalOpsAction[RuntimeVariantRow, RuntimeVariantData]):
    """Page through the runtime variant catalog."""

    searcher: RuntimeVariantSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_runtime_variants"

    @override
    def to_searcher(self) -> RuntimeVariantSearcher:
        return self.searcher
