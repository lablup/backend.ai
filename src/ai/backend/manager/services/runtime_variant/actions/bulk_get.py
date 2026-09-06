from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.queriers import BulkRuntimeVariantQuerier
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow


@dataclass
class PublicBulkGetRuntimeVariantsAction(
    PartialBulkGetEntityOpsAction[RuntimeVariantRow, RuntimeVariantData]
):
    """Read the runtime variants the caller named; every authenticated user may."""

    ids: Sequence[RuntimeVariantID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_bulk_get_runtime_variants"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkRuntimeVariantQuerier:
        return BulkRuntimeVariantQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
