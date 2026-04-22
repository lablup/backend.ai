from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from ai.backend.manager.services.metric.actions.live_stat import (
    KernelLiveStatAction,
    KernelLiveStatActionResult,
)
from ai.backend.manager.services.metric.service import UtilizationMetricService


class UtilizationMetricProcessors(AbstractProcessorPackage):
    query_container: ActionProcessor[ContainerMetricAction, ContainerMetricActionResult]
    query_container_metadata: ActionProcessor[
        ContainerMetricMetadataAction, ContainerMetricMetadataActionResult
    ]
    query_kernel_live_stat: ActionProcessor[KernelLiveStatAction, KernelLiveStatActionResult]

    def __init__(
        self,
        service: UtilizationMetricService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.query_container = ActionProcessor(service.query_metric, action_monitors)
        self.query_container_metadata = ActionProcessor(service.query_metadata, action_monitors)
        self.query_kernel_live_stat = ActionProcessor(
            service.query_kernel_live_stat_batch, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ContainerMetricAction.spec(),
            ContainerMetricMetadataAction.spec(),
            KernelLiveStatAction.spec(),
        ]
