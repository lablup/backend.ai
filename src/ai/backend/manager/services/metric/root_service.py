from ai.backend.manager.config.unified import ManagerUnifiedConfig

from .container_metric import ContainerUtilizationMetricService


class UtilizationMetricService:
    container: ContainerUtilizationMetricService

    def __init__(self, unified_config: ManagerUnifiedConfig) -> None:
        self.container = ContainerUtilizationMetricService(unified_config)
