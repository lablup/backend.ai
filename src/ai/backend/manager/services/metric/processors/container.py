from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)

from ..container_metric import MetricService


class MetricProcessors(ActionProcessor):
    query_metadata: ActionProcessor[
        ContainerMetricMetadataAction, ContainerMetricMetadataActionResult
    ]
    query_metric: ActionProcessor[ContainerMetricAction, ContainerMetricActionResult]

    def __init__(self, service: MetricService) -> None:
        self.query_metadata = ActionProcessor(service.query_metadata)
        self.query_metric = ActionProcessor(service.query_metric)
