from ai.backend.common.clients.prometheus.container_util.client import ContainerUtilizationReader
from ai.backend.common.clients.prometheus.device_util.client import DeviceUtilizationReader
from ai.backend.manager.repositories.metric.repository import MetricRepository

from .container_metric import ContainerUtilizationMetricService
from .device_metric import DeviceUtilizationMetricService


class UtilizationMetricService:
    container: ContainerUtilizationMetricService
    _metric_repository: MetricRepository

    def __init__(
        self,
        metric_repository: MetricRepository,
        container_utilization_reader: ContainerUtilizationReader,
        device_utilization_reader: DeviceUtilizationReader,
    ) -> None:
        self._metric_repository = metric_repository
        self.container = ContainerUtilizationMetricService(container_utilization_reader)
        self.device = DeviceUtilizationMetricService(device_utilization_reader)
