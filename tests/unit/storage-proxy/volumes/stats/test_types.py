from __future__ import annotations

from datetime import datetime

from ai.backend.storage.types import FSPerfMetric
from ai.backend.storage.volumes.stats.types import CachedFSPerfMetricData


class TestCachedFSPerfMetricData:
    """Tests for CachedFSPerfMetricData."""

    def test_from_metric_creates_correct_data(
        self,
        sample_metric: FSPerfMetric,
        sample_observed_at: datetime,
    ) -> None:
        cached = CachedFSPerfMetricData.from_metric(
            volume_name="vol1",
            metric=sample_metric,
            observed_at=sample_observed_at,
        )

        assert cached.volume_name == "vol1"
        assert cached.iops_read == sample_metric.iops_read
        assert cached.iops_write == sample_metric.iops_write
        assert cached.io_bytes_read == sample_metric.io_bytes_read
        assert cached.io_bytes_write == sample_metric.io_bytes_write
        assert cached.io_usec_read == sample_metric.io_usec_read
        assert cached.io_usec_write == sample_metric.io_usec_write
        assert cached.observed_at == sample_observed_at

    def test_to_metric_returns_correct_metric(
        self,
        sample_cached_data: CachedFSPerfMetricData,
        sample_metric: FSPerfMetric,
    ) -> None:
        metric = sample_cached_data.to_metric()

        assert metric.iops_read == sample_metric.iops_read
        assert metric.iops_write == sample_metric.iops_write
        assert metric.io_bytes_read == sample_metric.io_bytes_read
        assert metric.io_bytes_write == sample_metric.io_bytes_write
        assert metric.io_usec_read == sample_metric.io_usec_read
        assert metric.io_usec_write == sample_metric.io_usec_write

    def test_json_serialization_roundtrip(
        self,
        sample_cached_data: CachedFSPerfMetricData,
    ) -> None:
        json_str = sample_cached_data.model_dump_json()
        restored = CachedFSPerfMetricData.model_validate_json(json_str)

        assert restored.volume_name == sample_cached_data.volume_name
        assert restored.iops_read == sample_cached_data.iops_read
        assert restored.iops_write == sample_cached_data.iops_write
        assert restored.observed_at == sample_cached_data.observed_at
