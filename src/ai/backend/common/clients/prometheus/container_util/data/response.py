from dataclasses import dataclass

from ...data.response import ResultMetric, ResultValue


@dataclass
class ContainerUtilizationQueryResult:
    metric: ResultMetric
    values: list[ResultValue]
