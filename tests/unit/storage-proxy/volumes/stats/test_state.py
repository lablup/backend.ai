from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.storage.volumes.stats.state import VolumeState
from ai.backend.storage.volumes.stats.types import (
    CachedFSPerfMetricData,
    VolumeStatsObserverOptions,
)


class TestVolumeState:
    """Tests for VolumeState."""

    @pytest.fixture
    def state_with_cache_hit(
        self,
        mock_volume_pool_with_single_volume: MagicMock,
        mock_valkey_client: AsyncMock,
        default_options: VolumeStatsObserverOptions,
        sample_cached_data: CachedFSPerfMetricData,
    ) -> VolumeState:
        """VolumeState where cache returns data."""
        mock_valkey_client.get_volume_stats = AsyncMock(
            return_value=sample_cached_data.model_dump_json().encode()
        )
        return VolumeState(
            volume_pool=mock_volume_pool_with_single_volume,
            valkey_client=mock_valkey_client,
            options=default_options,
        )

    @pytest.fixture
    def state_with_cache_miss(
        self,
        mock_volume_pool_with_single_volume: MagicMock,
        mock_valkey_client: AsyncMock,
        default_options: VolumeStatsObserverOptions,
    ) -> VolumeState:
        """VolumeState where cache returns None."""
        mock_valkey_client.get_volume_stats = AsyncMock(return_value=None)
        return VolumeState(
            volume_pool=mock_volume_pool_with_single_volume,
            valkey_client=mock_valkey_client,
            options=default_options,
        )

    @pytest.fixture
    def state_with_cache_error(
        self,
        mock_volume_pool_with_single_volume: MagicMock,
        mock_valkey_client: AsyncMock,
        default_options: VolumeStatsObserverOptions,
    ) -> VolumeState:
        """VolumeState where cache raises exception."""
        mock_valkey_client.get_volume_stats = AsyncMock(side_effect=RuntimeError("Redis error"))
        return VolumeState(
            volume_pool=mock_volume_pool_with_single_volume,
            valkey_client=mock_valkey_client,
            options=default_options,
        )

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_data(
        self,
        state_with_cache_hit: VolumeState,
        mock_valkey_client: AsyncMock,
        sample_cached_data: CachedFSPerfMetricData,
    ) -> None:
        result = await state_with_cache_hit.get_performance_metric("test-volume")

        assert result.volume_name == sample_cached_data.volume_name
        assert result.iops_read == sample_cached_data.iops_read
        mock_valkey_client.get_volume_stats.assert_called_once_with("test-volume")

    @pytest.mark.asyncio
    async def test_cache_miss_calls_api_and_stores(
        self,
        state_with_cache_miss: VolumeState,
        mock_valkey_client: AsyncMock,
    ) -> None:
        result = await state_with_cache_miss.get_performance_metric("test-volume")

        assert result.volume_name == "test-volume"
        assert result.iops_read == 1000  # From sample_metric in fixture
        mock_valkey_client.set_volume_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_error_falls_back_to_api(
        self,
        state_with_cache_error: VolumeState,
        mock_valkey_client: AsyncMock,
    ) -> None:
        result = await state_with_cache_error.get_performance_metric("test-volume")

        assert result.volume_name == "test-volume"
        assert result.iops_read == 1000  # From sample_metric in fixture
        mock_valkey_client.set_volume_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_cache_failure_is_suppressed(
        self,
        mock_volume_pool_with_single_volume: MagicMock,
        mock_valkey_client: AsyncMock,
        default_options: VolumeStatsObserverOptions,
    ) -> None:
        mock_valkey_client.get_volume_stats = AsyncMock(return_value=None)
        mock_valkey_client.set_volume_stats = AsyncMock(
            side_effect=RuntimeError("Redis write error")
        )

        state = VolumeState(
            volume_pool=mock_volume_pool_with_single_volume,
            valkey_client=mock_valkey_client,
            options=default_options,
        )

        # Should not raise, just suppress the error
        result = await state.get_performance_metric("test-volume")

        assert result.volume_name == "test-volume"
        assert result.iops_read == 1000
