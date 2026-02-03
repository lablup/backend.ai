from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.storage.volumes.stats.observer import VolumeStatsObserver
from ai.backend.storage.volumes.stats.types import VolumeStatsObserverOptions


class TestVolumeStatsObserver:
    """Tests for VolumeStatsObserver."""

    @pytest.fixture
    def observer_with_single_volume(
        self,
        mock_volume_pool_with_single_volume: MagicMock,
        mock_valkey_client: AsyncMock,
        default_options: VolumeStatsObserverOptions,
    ) -> VolumeStatsObserver:
        """Observer configured with a single working volume."""
        return VolumeStatsObserver(
            volume_pool=mock_volume_pool_with_single_volume,
            valkey_client=mock_valkey_client,
            options=default_options,
        )

    @pytest.fixture
    def observer_with_empty_pool(
        self,
        mock_volume_pool_empty: MagicMock,
        mock_valkey_client: AsyncMock,
        default_options: VolumeStatsObserverOptions,
    ) -> VolumeStatsObserver:
        """Observer configured with no volumes."""
        return VolumeStatsObserver(
            volume_pool=mock_volume_pool_empty,
            valkey_client=mock_valkey_client,
            options=default_options,
        )

    @pytest.fixture
    def observer_with_timeout(
        self,
        mock_volume_pool_with_timeout: MagicMock,
        mock_valkey_client: AsyncMock,
    ) -> VolumeStatsObserver:
        """Observer configured with a volume that times out."""
        options = VolumeStatsObserverOptions(
            observe_interval=10.0,
            timeout_per_volume=0.1,  # Very short timeout
            cache_ttl=30.0,
        )
        return VolumeStatsObserver(
            volume_pool=mock_volume_pool_with_timeout,
            valkey_client=mock_valkey_client,
            options=options,
        )

    @pytest.fixture
    def observer_with_error(
        self,
        mock_volume_pool_with_error: MagicMock,
        mock_valkey_client: AsyncMock,
        default_options: VolumeStatsObserverOptions,
    ) -> VolumeStatsObserver:
        """Observer configured with a volume that raises error."""
        return VolumeStatsObserver(
            volume_pool=mock_volume_pool_with_error,
            valkey_client=mock_valkey_client,
            options=default_options,
        )

    def test_name_property(
        self,
        observer_with_single_volume: VolumeStatsObserver,
    ) -> None:
        assert observer_with_single_volume.name == "volume_stats"

    def test_observe_interval(
        self,
        observer_with_single_volume: VolumeStatsObserver,
    ) -> None:
        assert observer_with_single_volume.observe_interval() == 10.0

    def test_timeout(self) -> None:
        assert VolumeStatsObserver.timeout() == 30.0

    @pytest.mark.asyncio
    async def test_observe_with_empty_pool_does_nothing(
        self,
        observer_with_empty_pool: VolumeStatsObserver,
        mock_valkey_client: AsyncMock,
    ) -> None:
        await observer_with_empty_pool.observe()

        mock_valkey_client.set_volume_stats.assert_not_called()

    @pytest.mark.asyncio
    @patch("ai.backend.storage.volumes.stats.observer.VolumeStatsMetricObserver")
    @patch("ai.backend.storage.volumes.stats.observer.VolumePerfMetricObserver")
    async def test_observe_single_volume_success(
        self,
        mock_perf_observer_cls: MagicMock,
        mock_stats_observer_cls: MagicMock,
        observer_with_single_volume: VolumeStatsObserver,
        mock_valkey_client: AsyncMock,
    ) -> None:
        mock_stats_observer = MagicMock()
        mock_stats_observer_cls.instance.return_value = mock_stats_observer
        mock_perf_observer = MagicMock()
        mock_perf_observer_cls.instance.return_value = mock_perf_observer

        # Re-create observer to use mocked instances
        observer_with_single_volume._metric_observer = mock_stats_observer
        observer_with_single_volume._perf_metric_observer = mock_perf_observer

        await observer_with_single_volume.observe()

        mock_valkey_client.set_volume_stats.assert_called_once()
        mock_stats_observer.observe.assert_called_once()
        mock_perf_observer.update.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.storage.volumes.stats.observer.VolumeStatsMetricObserver")
    @patch("ai.backend.storage.volumes.stats.observer.VolumePerfMetricObserver")
    async def test_observe_timeout_records_failure(
        self,
        mock_perf_observer_cls: MagicMock,
        mock_stats_observer_cls: MagicMock,
        observer_with_timeout: VolumeStatsObserver,
        mock_valkey_client: AsyncMock,
    ) -> None:
        mock_stats_observer = MagicMock()
        mock_stats_observer_cls.instance.return_value = mock_stats_observer
        mock_perf_observer = MagicMock()
        mock_perf_observer_cls.instance.return_value = mock_perf_observer

        observer_with_timeout._metric_observer = mock_stats_observer
        observer_with_timeout._perf_metric_observer = mock_perf_observer

        await observer_with_timeout.observe()

        mock_valkey_client.set_volume_stats.assert_not_called()
        mock_stats_observer.observe.assert_called_once()
        call_kwargs = mock_stats_observer.observe.call_args.kwargs
        assert call_kwargs["status"] == "failure"

    @pytest.mark.asyncio
    @patch("ai.backend.storage.volumes.stats.observer.VolumeStatsMetricObserver")
    @patch("ai.backend.storage.volumes.stats.observer.VolumePerfMetricObserver")
    async def test_observe_error_records_failure(
        self,
        mock_perf_observer_cls: MagicMock,
        mock_stats_observer_cls: MagicMock,
        observer_with_error: VolumeStatsObserver,
        mock_valkey_client: AsyncMock,
    ) -> None:
        mock_stats_observer = MagicMock()
        mock_stats_observer_cls.instance.return_value = mock_stats_observer
        mock_perf_observer = MagicMock()
        mock_perf_observer_cls.instance.return_value = mock_perf_observer

        observer_with_error._metric_observer = mock_stats_observer
        observer_with_error._perf_metric_observer = mock_perf_observer

        await observer_with_error.observe()

        mock_valkey_client.set_volume_stats.assert_not_called()
        mock_stats_observer.observe.assert_called_once()
        call_kwargs = mock_stats_observer.observe.call_args.kwargs
        assert call_kwargs["status"] == "failure"

    @pytest.mark.asyncio
    async def test_cleanup_does_nothing(
        self,
        observer_with_single_volume: VolumeStatsObserver,
    ) -> None:
        # cleanup should not raise
        await observer_with_single_volume.cleanup()
