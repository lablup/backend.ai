from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)

from ..container_metric import ContainerUtilizationMetricService


class ContainerUtilizationMetricProcessors(ActionProcessor):
    query_metadata: ActionProcessor[
        ContainerMetricMetadataAction, ContainerMetricMetadataActionResult
    ]
    query_metric: ActionProcessor[ContainerMetricAction, ContainerMetricActionResult]

    def __init__(
        self, service: ContainerUtilizationMetricService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.query_metadata = ActionProcessor(service.query_metadata, action_monitors)
        self.query_metric = ActionProcessor(service.query_metric, action_monitors)
