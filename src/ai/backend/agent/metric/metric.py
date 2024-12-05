from prometheus_client import generate_latest

from ai.backend.common.metric.metric import CommonMetric


class MetricRegistry:
    """
    Metric registry for the agent service.
    """

    common: CommonMetric

    def __init__(self) -> None:
        self.common = CommonMetric.instance()

    def to_prometheus(self) -> str:
        self.common.update()
        return generate_latest().decode("utf-8")
