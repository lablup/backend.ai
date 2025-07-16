from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.metric.repository import MetricRepository

from .container_metric import ContainerUtilizationMetricService


class UtilizationMetricService:
    container: ContainerUtilizationMetricService
    _metric_repository: MetricRepository

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        metric_repository: MetricRepository,
    ) -> None:
        self.container = ContainerUtilizationMetricService(config_provider)
        self._metric_repository = metric_repository
