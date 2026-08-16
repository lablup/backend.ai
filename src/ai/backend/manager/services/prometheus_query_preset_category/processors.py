from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
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
from ai.backend.manager.services.prometheus_query_preset_category.actions.search import (
    SearchCategoriesAction,
)


class PrometheusQueryPresetCategoryProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    global_create_category: GlobalActionProcessor[
        CreateCategoryAction,
        CreatedEntityOpsResult[PrometheusQueryPresetCategoryData],
    ]
    global_get_category: GlobalActionProcessor[
        GetCategoryAction,
        EntityOpsResult[PrometheusQueryPresetCategoryData],
    ]
    global_search_categories: GlobalActionProcessor[
        SearchCategoriesAction,
        BatchOpsResult[PrometheusQueryPresetCategoryData],
    ]
    purge_category: SingleEntityActionProcessor[
        PurgeCategoryAction,
        EntityOpsResult[PrometheusQueryPresetCategoryData],
    ]

    def __init__(self, group: ProcessorGroup[PrometheusQueryPresetCategoryData]) -> None:
        self.global_create_category = group.global_create_ops(CreateCategoryAction)
        self.global_get_category = group.global_get_ops(GetCategoryAction)
        self.global_search_categories = group.global_search_ops(SearchCategoriesAction)
        self.purge_category = group.entity_purge_ops(PurgeCategoryAction)
