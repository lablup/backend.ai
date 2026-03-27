from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from ai.backend.storage.types import FSPerfMetric


@dataclass
class VolumeStatsObserverOptions:
    """Volume stats observer configuration."""

    observe_interval: float = 10.0
    timeout_per_volume: float = 5.0
    cache_ttl: float = 30.0


class CachedFSPerfMetricData(BaseModel):
    """Cached performance metric with metadata for Redis serialization."""

    volume_name: str
    iops_read: int
    iops_write: int
    io_bytes_read: int
    io_bytes_write: int
    io_usec_read: float
    io_usec_write: float
    observed_at: datetime

    @classmethod
    def from_metric(
        cls,
        volume_name: str,
        metric: FSPerfMetric,
        observed_at: datetime,
    ) -> CachedFSPerfMetricData:
        return cls(
            volume_name=volume_name,
            iops_read=metric.iops_read,
            iops_write=metric.iops_write,
            io_bytes_read=metric.io_bytes_read,
            io_bytes_write=metric.io_bytes_write,
            io_usec_read=metric.io_usec_read,
            io_usec_write=metric.io_usec_write,
            observed_at=observed_at,
        )

    def to_metric(self) -> FSPerfMetric:
        return FSPerfMetric(
            iops_read=self.iops_read,
            iops_write=self.iops_write,
            io_bytes_read=self.io_bytes_read,
            io_bytes_write=self.io_bytes_write,
            io_usec_read=self.io_usec_read,
            io_usec_write=self.io_usec_write,
        )
