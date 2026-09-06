from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.queriers import (
    BulkPrometheusQueryPresetCategoryQuerier,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)


@dataclass
class PublicBulkGetCategoriesAction(
    PartialBulkGetEntityOpsAction[
        PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData
    ]
):
    """Read the categories the caller named; every authenticated user may."""

    ids: Sequence[PrometheusQueryPresetCategoryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_bulk_get_prometheus_query_preset_categories"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkPrometheusQueryPresetCategoryQuerier:
        return BulkPrometheusQueryPresetCategoryQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
