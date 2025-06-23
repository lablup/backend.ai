from ai.backend.manager.config.provider import ManagerConfigProvider

from .container_metric import ContainerUtilizationMetricService


class UtilizationMetricService:
    container: ContainerUtilizationMetricService

    def __init__(self, config_provider: ManagerConfigProvider) -> None:
        self.container = ContainerUtilizationMetricService(config_provider)
