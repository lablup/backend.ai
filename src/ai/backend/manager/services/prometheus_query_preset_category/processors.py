from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    PublicSingleEntityActionProcessor,
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.prometheus_query_preset_category.types import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions.bulk_get import (
    PublicBulkGetCategoriesAction,
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
    public_get_category: PublicSingleEntityActionProcessor[
        GetCategoryAction,
        EntityOpsResult[PrometheusQueryPresetCategoryData],
    ]
    public_bulk_get_categories: PartialBulkActionProcessor[
        PublicBulkGetCategoriesAction,
        PrometheusQueryPresetCategoryData,
    ]
    public_search_categories: PublicActionProcessor[
        SearchCategoriesAction,
        BatchOpsResult[PrometheusQueryPresetCategoryData],
    ]
    purge_category: SingleEntityActionProcessor[
        PurgeCategoryAction,
        EntityOpsResult[PrometheusQueryPresetCategoryData],
    ]

    def __init__(self, group: ProcessorGroup[PrometheusQueryPresetCategoryData]) -> None:
        self.global_create_category = group.global_create_ops(CreateCategoryAction)
        self.public_get_category = group.public_get_ops(GetCategoryAction)
        self.public_bulk_get_categories = group.public_partial_bulk_get_ops(
            PublicBulkGetCategoriesAction
        )
        self.public_search_categories = group.public_search_ops(SearchCategoriesAction)
        self.purge_category = group.entity_purge_ops(PurgeCategoryAction)
