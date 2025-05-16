from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)

from ..root_service import UtilizationMetricService


class UtilizationMetricProcessors(AbstractProcessorPackage):
    query_container: ActionProcessor[ContainerMetricAction, ContainerMetricActionResult]
    query_container_metadata: ActionProcessor[
        ContainerMetricMetadataAction, ContainerMetricMetadataActionResult
    ]

    def __init__(
        self, service: UtilizationMetricService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.query_container = ActionProcessor(service.container.query_metric, action_monitors)
        self.query_container_metadata = ActionProcessor(
            service.container.query_metadata, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ContainerMetricAction.spec(),
            ContainerMetricMetadataAction.spec(),
        ]
