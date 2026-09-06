from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.field.bulk_processor import BulkFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.services.metric.actions.batch_get_kernel_live_stats import (
    BatchGetKernelLiveStatsAction,
    BatchGetKernelLiveStatsActionResult,
)
from ai.backend.manager.services.metric.actions.search_container_metric_metadata import (
    PublicSearchContainerMetricMetadataAction,
    PublicSearchContainerMetricMetadataActionResult,
)
from ai.backend.manager.services.metric.actions.search_container_metrics import (
    GlobalSearchContainerMetricsAction,
    GlobalSearchContainerMetricsActionResult,
)
from ai.backend.manager.services.metric.actions.search_user_container_metrics import (
    SearchUserContainerMetricsAction,
    SearchUserContainerMetricsActionResult,
)
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_owner import (
    LookupBulkKernelOwnerAction,
)


class MetricProcessors:
    """Container utilization as Prometheus answers it.

    Every read reaches the metric store rather than a table, so the service stays and
    nothing runs against ops. The metric names are a query fixed in code, answered for
    the same entity a stored query preset is and open to any authenticated caller.

    A user's own metrics are answered for that user; reading across users names none, so
    it stays global. The live stats are read per kernel, and a kernel is a row of the
    session running it, so that read resolves those sessions first and each answers for
    it.
    """

    search_user_container_metrics: SingleEntityActionProcessor[
        SearchUserContainerMetricsAction, SearchUserContainerMetricsActionResult
    ]
    global_search: GlobalActionProcessor[
        GlobalSearchContainerMetricsAction, GlobalSearchContainerMetricsActionResult
    ]
    metadata_public_search: PublicActionProcessor[
        PublicSearchContainerMetricMetadataAction,
        PublicSearchContainerMetricMetadataActionResult,
    ]
    batch_get_kernel_live_stats: BulkFieldActionProcessor[
        BatchGetKernelLiveStatsAction, BatchGetKernelLiveStatsActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[Any],
        user_group: ProcessorGroup[Any],
        session_group: ProcessorGroup[Any],
        service: MetricService,
    ) -> None:
        self.search_user_container_metrics = user_group.single_entity(
            SearchUserContainerMetricsAction, service.search_user_container_metrics
        )
        self.global_search = group.global_scope(
            GlobalSearchContainerMetricsAction, service.global_search_container_metrics
        )
        self.metadata_public_search = group.public(
            PublicSearchContainerMetricMetadataAction, service.search_container_metric_metadata
        )
        self.batch_get_kernel_live_stats = session_group.atomic_bulk_field(
            BatchGetKernelLiveStatsAction,
            LookupBulkKernelOwnerAction,
            service.batch_get_kernel_live_stats,
        )
