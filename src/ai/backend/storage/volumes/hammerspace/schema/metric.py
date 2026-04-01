from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ClusterMetricRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    time: int  # timestamp
    total: int | None
    used: int | None
    free: int | None

    def parse(self) -> ValidClusterMetricRow | None:
        if self.total is None or self.used is None or self.free is None:
            return None
        return ValidClusterMetricRow(
            time=self.time,
            total=self.total,
            used=self.used,
            free=self.free,
        )


class ValidClusterMetricRow(BaseModel):
    time: int  # timestamp
    total: int
    used: int
    free: int


class MetricSeries(BaseModel):
    model_config = ConfigDict(extra="allow")

    tags: dict[str, str]
    rows: list[ClusterMetricRow]


class Metric(BaseModel):
    model_config = ConfigDict(extra="allow")

    series: list[MetricSeries]
