from ai.backend.manager.config.shared import ManagerSharedConfig

from .container_metric import ContainerUtilizationMetricService


class UtilizationMetricService:
    container: ContainerUtilizationMetricService

    def __init__(self, shared_config: ManagerSharedConfig) -> None:
        self.container = ContainerUtilizationMetricService(shared_config)
