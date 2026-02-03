"""Volume stats metrics for monitoring storage performance observation."""

from __future__ import annotations

from typing import Self

from prometheus_client import Counter, Histogram


class VolumeStatsMetricObserver:
    """Prometheus metrics for volume stats observation."""

    _instance: Self | None = None

    _observe_total: Counter
    _observe_duration_seconds: Histogram

    def __init__(self) -> None:
        self._observe_total = Counter(
            name="backendai_storage_volume_stats_observe_total",
            documentation="Total number of volume stats observation attempts",
            labelnames=["volume", "status"],
        )
        self._observe_duration_seconds = Histogram(
            name="backendai_storage_volume_stats_observe_duration_seconds",
            documentation="Duration of volume stats observation in seconds",
            labelnames=["volume"],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
        )

    @classmethod
    def instance(cls) -> Self:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe(
        self,
        *,
        volume: str,
        status: str,
        duration: float,
    ) -> None:
        """
        Record a volume stats observation.

        Args:
            volume: The volume name
            status: The observation status ('success' or 'failure')
            duration: The observation duration in seconds
        """
        self._observe_total.labels(volume=volume, status=status).inc()
        self._observe_duration_seconds.labels(volume=volume).observe(duration)
