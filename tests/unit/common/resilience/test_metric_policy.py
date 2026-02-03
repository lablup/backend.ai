from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.resilience import Resilience


class TestMetricPolicy:
    @pytest.mark.asyncio
    async def test_successful_operation_metrics(self, mocker: MockerFixture) -> None:
        """Test that successful operations record correct metrics."""
        mock_observer = MagicMock()
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )

        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def successful_operation() -> str:
            return "success"

        result = await successful_operation()

        assert result == "success"
        # Operation name should be auto-extracted from function name
        mock_observer.observe_layer_operation_triggered.assert_called_once_with(
            domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT, operation="successful_operation"
        )
        mock_observer.observe_layer_operation.assert_called_once()
        call_kwargs = mock_observer.observe_layer_operation.call_args.kwargs
        assert call_kwargs["domain"] == DomainType.CLIENT
        assert call_kwargs["layer"] == LayerType.AGENT_CLIENT
        assert call_kwargs["operation"] == "successful_operation"
        assert call_kwargs["exception"] is None
        assert call_kwargs["duration"] > 0

    @pytest.mark.asyncio
    async def test_failed_operation_metrics(self, mocker: MockerFixture) -> None:
        """Test that failed operations record failure metrics."""
        mock_observer = MagicMock()
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )

        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def failing_operation() -> str:
            raise ValueError("Operation failed")

        with pytest.raises(ValueError, match="Operation failed"):
            await failing_operation()

        # Operation name should be auto-extracted from function name
        mock_observer.observe_layer_operation_triggered.assert_called_once_with(
            domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT, operation="failing_operation"
        )
        mock_observer.observe_layer_operation.assert_called_once()
        call_kwargs = mock_observer.observe_layer_operation.call_args.kwargs
        assert call_kwargs["domain"] == DomainType.CLIENT
        assert call_kwargs["layer"] == LayerType.AGENT_CLIENT
        assert call_kwargs["operation"] == "failing_operation"
        assert call_kwargs["exception"] is not None
        assert call_kwargs["duration"] > 0

    @pytest.mark.asyncio
    async def test_metric_duration_tracking(self, mocker: MockerFixture) -> None:
        """Test that metric policy correctly tracks operation duration."""
        mock_observer = MagicMock()
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )

        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def timed_operation() -> str:
            await asyncio.sleep(0.1)
            return "success"

        result = await timed_operation()

        assert result == "success"
        call_kwargs = mock_observer.observe_layer_operation.call_args.kwargs
        # Duration should be at least 0.1s
        assert call_kwargs["duration"] >= 0.1

    @pytest.mark.asyncio
    async def test_auto_operation_name_from_context(self, mocker: MockerFixture) -> None:
        """Test that operation name is automatically extracted from function name via context."""
        mock_observer = MagicMock()
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )

        # Create MetricPolicy without operation parameter
        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_SESSION)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def my_valkey_operation() -> str:
            return "success"

        result = await my_valkey_operation()

        assert result == "success"
        # Operation name should be automatically extracted from function name
        mock_observer.observe_layer_operation_triggered.assert_called_once_with(
            domain=DomainType.VALKEY,
            layer=LayerType.VALKEY_SESSION,
            operation="my_valkey_operation",
        )
        call_kwargs = mock_observer.observe_layer_operation.call_args.kwargs
        assert call_kwargs["operation"] == "my_valkey_operation"
