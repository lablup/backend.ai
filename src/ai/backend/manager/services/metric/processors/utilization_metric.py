from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.metric.actions.container import (
    ContainerCurrentMetricAction,
    ContainerCurrentMetricActionResult,
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from ai.backend.manager.services.metric.actions.device import (
    DeviceCurrentMetricAction,
    DeviceCurrentMetricActionResult,
    DeviceMetricAction,
    DeviceMetricActionResult,
    DeviceMetricMetadataAction,
    DeviceMetricMetadataActionResult,
)

from ..root_service import UtilizationMetricService


class UtilizationMetricProcessors(AbstractProcessorPackage):
    query_container: ActionProcessor[ContainerMetricAction, ContainerMetricActionResult]
    query_container_current: ActionProcessor[
        ContainerCurrentMetricAction, ContainerCurrentMetricActionResult
    ]
    query_container_metadata: ActionProcessor[
        ContainerMetricMetadataAction, ContainerMetricMetadataActionResult
    ]

    query_device: ActionProcessor[DeviceMetricAction, DeviceMetricActionResult]
    query_device_current: ActionProcessor[
        DeviceCurrentMetricAction, DeviceCurrentMetricActionResult
    ]
    query_device_metadata: ActionProcessor[
        DeviceMetricMetadataAction, DeviceMetricMetadataActionResult
    ]

    def __init__(
        self, service: UtilizationMetricService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.query_container = ActionProcessor(service.container.query_metric, action_monitors)
        self.query_container_current = ActionProcessor(
            service.container.query_current_metric, action_monitors
        )
        self.query_container_metadata = ActionProcessor(
            service.container.query_metadata, action_monitors
        )
        self.query_device = ActionProcessor(service.device.query_metric, action_monitors)
        self.query_device_current = ActionProcessor(
            service.device.query_current_metric, action_monitors
        )
        self.query_device_metadata = ActionProcessor(service.device.query_metadata, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ContainerMetricAction.spec(),
            ContainerCurrentMetricAction.spec(),
            ContainerMetricMetadataAction.spec(),
            DeviceMetricAction.spec(),
            DeviceCurrentMetricAction.spec(),
            DeviceMetricMetadataAction.spec(),
        ]
