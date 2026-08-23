from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.field.bulk_processor import BulkFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import PublicActionProcessor
from ai.backend.manager.services.metric.actions.batch_get_kernel_live_stats import (
    BatchGetKernelLiveStatsAction,
    BatchGetKernelLiveStatsActionResult,
)
from ai.backend.manager.services.metric.actions.search_container_metric_metadata import (
    PublicSearchContainerMetricMetadataAction,
    PublicSearchContainerMetricMetadataActionResult,
)
from ai.backend.manager.services.metric.actions.search_container_metrics import (
    PublicSearchContainerMetricsAction,
    PublicSearchContainerMetricsActionResult,
)
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_owner import (
    LookupBulkKernelOwnerAction,
)


class MetricProcessors:
    """Container utilization as Prometheus answers it.

    Every read reaches the metric store rather than a table, so the service stays and
    nothing runs against ops. The two searches are queries fixed in code, so they answer
    for the same entity a stored query preset does, and both are open to any
    authenticated caller; what one sees of another user's containers is narrowed by the
    labels the adapter fills in.

    The live stats are read per kernel, and a kernel is a row of the session running it,
    so that read resolves those sessions first and each answers for it.
    """

    public_search: PublicActionProcessor[
        PublicSearchContainerMetricsAction, PublicSearchContainerMetricsActionResult
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
        session_group: ProcessorGroup[Any],
        service: MetricService,
    ) -> None:
        self.public_search = group.public(
            PublicSearchContainerMetricsAction, service.search_container_metrics
        )
        self.metadata_public_search = group.public(
            PublicSearchContainerMetricMetadataAction, service.search_container_metric_metadata
        )
        self.batch_get_kernel_live_stats = session_group.atomic_bulk_field(
            BatchGetKernelLiveStatsAction,
            LookupBulkKernelOwnerAction,
            service.batch_get_kernel_live_stats,
        )
