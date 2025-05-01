from ai.backend.manager.config.shared import SharedManagerConfig

from .container_metric import ContainerUtilizationMetricService


class UtilizationMetricService:
    container: ContainerUtilizationMetricService

    def __init__(self, shared_config: SharedManagerConfig) -> None:
        self.container = ContainerUtilizationMetricService(shared_config)
