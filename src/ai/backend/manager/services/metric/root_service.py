from ai.backend.manager.config import SharedConfig

from .container_metric import ContainerUtilizationMetricService


class UtilizationMetricService:
    container: ContainerUtilizationMetricService

    def __init__(self, shared_config: SharedConfig) -> None:
        self.container = ContainerUtilizationMetricService(shared_config)
