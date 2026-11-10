from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.purgers import (
    PrometheusQueryPresetCategoryPurger,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)


@dataclass(frozen=True)
class PartialBulkPurgeCategoriesAction(
    PartialBulkPurgeEntityOpsAction[
        PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData
    ]
):
    """Remove the named categories from the catalog, answering for each one."""

    ids: Sequence[PrometheusQueryPresetCategoryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_prometheus_query_preset_categories"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, PrometheusQueryPresetCategoryPurger]:
        return {
            category_id: PrometheusQueryPresetCategoryPurger(category_id=category_id)
            for category_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, ids=[category_id for category_id in self.ids if category_id in allowed]
        )
