"""Volume performance metrics for Prometheus exposition."""

from __future__ import annotations

from datetime import datetime
from typing import Self

from prometheus_client import Gauge


class VolumePerfMetricObserver:
    """Prometheus Gauge metrics for volume performance data."""

    _instance: Self | None = None

    _iops_read: Gauge
    _iops_write: Gauge
    _throughput_bytes_read: Gauge
    _throughput_bytes_write: Gauge
    _latency_usec_read: Gauge
    _latency_usec_write: Gauge
    _last_updated_timestamp: Gauge

    def __init__(self) -> None:
        self._iops_read = Gauge(
            name="backendai_storage_volume_iops_read",
            documentation="Read IOPS for the volume",
            labelnames=["volume"],
        )
        self._iops_write = Gauge(
            name="backendai_storage_volume_iops_write",
            documentation="Write IOPS for the volume",
            labelnames=["volume"],
        )
        self._throughput_bytes_read = Gauge(
            name="backendai_storage_volume_throughput_bytes_read",
            documentation="Read throughput in bytes per second for the volume",
            labelnames=["volume"],
        )
        self._throughput_bytes_write = Gauge(
            name="backendai_storage_volume_throughput_bytes_write",
            documentation="Write throughput in bytes per second for the volume",
            labelnames=["volume"],
        )
        self._latency_usec_read = Gauge(
            name="backendai_storage_volume_latency_usec_read",
            documentation="Read latency in microseconds for the volume",
            labelnames=["volume"],
        )
        self._latency_usec_write = Gauge(
            name="backendai_storage_volume_latency_usec_write",
            documentation="Write latency in microseconds for the volume",
            labelnames=["volume"],
        )
        self._last_updated_timestamp = Gauge(
            name="backendai_storage_volume_metric_last_updated_timestamp",
            documentation="Unix timestamp of the last metric update for the volume",
            labelnames=["volume"],
        )

    @classmethod
    def instance(cls) -> Self:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def update(
        self,
        *,
        volume: str,
        iops_read: int,
        iops_write: int,
        io_bytes_read: int,
        io_bytes_write: int,
        io_usec_read: float,
        io_usec_write: float,
        observed_at: datetime,
    ) -> None:
        """
        Update volume performance metrics.

        Args:
            volume: The volume name
            iops_read: Read IOPS
            iops_write: Write IOPS
            io_bytes_read: Read throughput in bytes
            io_bytes_write: Write throughput in bytes
            io_usec_read: Read latency in microseconds
            io_usec_write: Write latency in microseconds
            observed_at: Timestamp of the observation
        """
        self._iops_read.labels(volume=volume).set(iops_read)
        self._iops_write.labels(volume=volume).set(iops_write)
        self._throughput_bytes_read.labels(volume=volume).set(io_bytes_read)
        self._throughput_bytes_write.labels(volume=volume).set(io_bytes_write)
        self._latency_usec_read.labels(volume=volume).set(io_usec_read)
        self._latency_usec_write.labels(volume=volume).set(io_usec_write)
        self._last_updated_timestamp.labels(volume=volume).set(observed_at.timestamp())
