from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Protocol
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.storage.types import FSPerfMetric
from ai.backend.storage.volumes.stats.types import (
    CachedFSPerfMetricData,
    VolumeStatsObserverOptions,
)


class MockVolume(Protocol):
    async def get_performance_metric(self) -> FSPerfMetric: ...


@pytest.fixture
def sample_metric() -> FSPerfMetric:
    """Sample FSPerfMetric for testing."""
    return FSPerfMetric(
        iops_read=1000,
        iops_write=500,
        io_bytes_read=1024000,
        io_bytes_write=512000,
        io_usec_read=100.5,
        io_usec_write=200.3,
    )


@pytest.fixture
def sample_observed_at() -> datetime:
    """Sample observation timestamp."""
    return datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)


@pytest.fixture
def sample_cached_data(
    sample_metric: FSPerfMetric,
    sample_observed_at: datetime,
) -> CachedFSPerfMetricData:
    """Sample cached metric data."""
    return CachedFSPerfMetricData.from_metric(
        volume_name="test-volume",
        metric=sample_metric,
        observed_at=sample_observed_at,
    )


@pytest.fixture
def default_options() -> VolumeStatsObserverOptions:
    """Default observer options for testing."""
    return VolumeStatsObserverOptions(
        observe_interval=10.0,
        timeout_per_volume=5.0,
        cache_ttl=30.0,
    )


@pytest.fixture
def mock_valkey_client() -> AsyncMock:
    """Mock ValkeyVolumeStatsClient."""
    client = AsyncMock()
    client.get_volume_stats = AsyncMock(return_value=None)
    client.set_volume_stats = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_volume_pool_with_single_volume(sample_metric: FSPerfMetric) -> MagicMock:
    """Mock VolumePool with a single volume."""
    mock_volume = AsyncMock()
    mock_volume.get_performance_metric = AsyncMock(return_value=sample_metric)

    @asynccontextmanager
    async def get_volume_by_name(name: str) -> AsyncIterator[MockVolume]:
        yield mock_volume

    pool = MagicMock()
    pool.list_volumes = MagicMock(return_value={"test-volume": MagicMock()})
    pool.get_volume_by_name = get_volume_by_name

    return pool


@pytest.fixture
def mock_volume_pool_empty() -> MagicMock:
    """Mock VolumePool with no volumes."""
    pool = MagicMock()
    pool.list_volumes = MagicMock(return_value={})
    return pool


@pytest.fixture
def mock_volume_pool_with_timeout() -> MagicMock:
    """Mock VolumePool where volume API times out."""
    mock_volume = AsyncMock()

    async def slow_get_metric() -> FSPerfMetric:
        await asyncio.sleep(10)  # Will exceed timeout
        return FSPerfMetric(
            iops_read=0,
            iops_write=0,
            io_bytes_read=0,
            io_bytes_write=0,
            io_usec_read=0,
            io_usec_write=0,
        )

    mock_volume.get_performance_metric = slow_get_metric

    @asynccontextmanager
    async def get_volume_by_name(name: str) -> AsyncIterator[MockVolume]:
        yield mock_volume

    pool = MagicMock()
    pool.list_volumes = MagicMock(return_value={"slow-volume": MagicMock()})
    pool.get_volume_by_name = get_volume_by_name

    return pool


@pytest.fixture
def mock_volume_pool_with_error() -> MagicMock:
    """Mock VolumePool where volume API raises exception."""
    mock_volume = AsyncMock()
    mock_volume.get_performance_metric = AsyncMock(side_effect=RuntimeError("API error"))

    @asynccontextmanager
    async def get_volume_by_name(name: str) -> AsyncIterator[MockVolume]:
        yield mock_volume

    pool = MagicMock()
    pool.list_volumes = MagicMock(return_value={"error-volume": MagicMock()})
    pool.get_volume_by_name = get_volume_by_name

    return pool
