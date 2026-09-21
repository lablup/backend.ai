from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions.bulk_get import (
    BulkGetCategoriesAction,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions.create import (
    CreateCategoryAction,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions.get import (
    GetCategoryAction,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions.purge import (
    PurgeCategoryAction,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions.scoped_search import (
    ScopedSearchCategoriesAction,
)


class PrometheusQueryPresetCategoryProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    global_create_category: GlobalActionProcessor[
        CreateCategoryAction,
        CreatedEntityOpsResult[PrometheusQueryPresetCategoryData],
    ]
    get_category: SingleEntityActionProcessor[
        GetCategoryAction,
        EntityOpsResult[PrometheusQueryPresetCategoryData],
    ]
    bulk_get_categories: PartialBulkActionProcessor[
        BulkGetCategoriesAction,
        PrometheusQueryPresetCategoryData,
    ]
    scoped_search_categories: ScopeActionProcessor[
        ScopedSearchCategoriesAction,
        ScopedBatchOpsResult[PrometheusQueryPresetCategoryData],
    ]
    purge_category: SingleEntityActionProcessor[
        PurgeCategoryAction,
        EntityOpsResult[PrometheusQueryPresetCategoryData],
    ]

    def __init__(self, group: ProcessorGroup[PrometheusQueryPresetCategoryData]) -> None:
        self.global_create_category = group.global_create_ops(CreateCategoryAction)
        self.get_category = group.single_get_ops(GetCategoryAction)
        self.bulk_get_categories = group.partial_bulk_get_ops(BulkGetCategoriesAction)
        self.scoped_search_categories = group.scoped_search_ops(ScopedSearchCategoriesAction)
        self.purge_category = group.entity_purge_ops(PurgeCategoryAction)
