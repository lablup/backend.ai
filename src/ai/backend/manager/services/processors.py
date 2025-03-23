from ai.backend.manager.services.metric.container_metric import (
    MetricService as ContainerMetricService,
)
from ai.backend.manager.services.metric.processors.container import (
    MetricProcessors as ContainerMetricProcessors,
)


class Processors:
    container_metric: ContainerMetricProcessors

    def __init__(
        self,
        container_metric_service: ContainerMetricService,
    ) -> None:
        self.container_metric = ContainerMetricProcessors(container_metric_service)
