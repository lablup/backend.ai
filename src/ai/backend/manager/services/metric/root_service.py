from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.manager.repositories.metric.repository import MetricRepository

from .container_metric import ContainerUtilizationMetricService


class UtilizationMetricService:
    container: ContainerUtilizationMetricService
    _metric_repository: MetricRepository

    def __init__(
        self,
        prometheus_client: PrometheusClient,
        timewindow: str,
        metric_repository: MetricRepository,
    ) -> None:
        self.container = ContainerUtilizationMetricService(prometheus_client, timewindow=timewindow)
        self._metric_repository = metric_repository
