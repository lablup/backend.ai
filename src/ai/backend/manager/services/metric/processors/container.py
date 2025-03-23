from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricLabelValuesAction,
    ContainerMetricLabelValuesActionResult,
)

from ..container_metric import MetricService


class MetricProcessors(ActionProcessor):
    query_label_values: ActionProcessor[
        ContainerMetricLabelValuesAction, ContainerMetricLabelValuesActionResult
    ]
    query_metric: ActionProcessor[ContainerMetricAction, ContainerMetricActionResult]

    def __init__(self, service: MetricService) -> None:
        self.query_label_values = ActionProcessor(service.query_label_values)
        self.query_metric = ActionProcessor(service.query_metric)
