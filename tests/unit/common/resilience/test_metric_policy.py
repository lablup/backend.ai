from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.resilience import Resilience


class TestMetricPolicy:
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

    async def test_safe_observe_suppresses_trigger_metric_errors(
        self, mocker: MockerFixture
    ) -> None:
        """Test that _safe_observe suppresses errors from observe_layer_operation_triggered."""
        mock_observer = MagicMock()
        mock_observer.observe_layer_operation_triggered.side_effect = ValueError(
            "mmap slice assignment is wrong size"
        )
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
        mock_observer.observe_layer_operation_triggered.assert_called_once()

    async def test_safe_observe_suppresses_completion_metric_errors(
        self, mocker: MockerFixture
    ) -> None:
        """Test that _safe_observe suppresses errors from observe_layer_operation on success."""
        mock_observer = MagicMock()
        mock_observer.observe_layer_operation.side_effect = ValueError(
            "mmap slice assignment is wrong size"
        )
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
        mock_observer.observe_layer_operation.assert_called_once()

    async def test_safe_observe_suppresses_failure_path_metric_errors(
        self, mocker: MockerFixture
    ) -> None:
        """Test that when the operation fails AND metric recording also fails,
        the original operation exception propagates (not the metric error)."""
        mock_observer = MagicMock()
        mock_observer.observe_layer_operation.side_effect = ValueError(
            "mmap slice assignment is wrong size"
        )
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )

        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def failing_operation() -> str:
            raise RuntimeError("connection lost")

        with pytest.raises(RuntimeError, match="connection lost"):
            await failing_operation()

    async def test_safe_observe_suppresses_all_metric_errors(self, mocker: MockerFixture) -> None:
        """Test that when both trigger and completion metrics fail, the operation succeeds."""
        mock_observer = MagicMock()
        mmap_error = ValueError("mmap slice assignment is wrong size")
        mock_observer.observe_layer_operation_triggered.side_effect = mmap_error
        mock_observer.observe_layer_operation.side_effect = mmap_error
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

    async def test_cancelled_error_propagates_through_metric_policy(
        self, mocker: MockerFixture
    ) -> None:
        """Test that CancelledError (BaseException) propagates correctly."""
        mock_observer = MagicMock()
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )

        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def cancelled_operation() -> str:
            raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await cancelled_operation()

        mock_observer.observe_layer_operation.assert_called_once()
        call_kwargs = mock_observer.observe_layer_operation.call_args.kwargs
        assert isinstance(call_kwargs["exception"], asyncio.CancelledError)

    async def test_metric_error_logged_once_as_warning(self, mocker: MockerFixture) -> None:
        """Test that the first metric error is logged at warning level,
        and subsequent errors are silently suppressed."""
        mock_observer = MagicMock()
        mock_observer.observe_layer_operation_triggered.side_effect = ValueError(
            "mmap slice assignment is wrong size"
        )
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )
        mock_log_warning = mocker.patch(
            "ai.backend.common.resilience.policies.metrics.log.warning",
        )

        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def operation() -> str:
            return "ok"

        await operation()
        await operation()
        await operation()

        # Warning should be logged only once despite 3 calls (3 trigger + 3 completion)
        assert mock_log_warning.call_count == 1

    async def test_operation_error_propagates_when_trigger_metric_fails(
        self, mocker: MockerFixture
    ) -> None:
        """Test that when trigger metric fails and the operation also fails,
        the original operation exception propagates."""
        mock_observer = MagicMock()
        mock_observer.observe_layer_operation_triggered.side_effect = ValueError(
            "mmap slice assignment is wrong size"
        )
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )

        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def failing_operation() -> str:
            raise RuntimeError("connection lost")

        with pytest.raises(RuntimeError, match="connection lost"):
            await failing_operation()

    async def test_operation_error_propagates_when_all_metrics_fail(
        self, mocker: MockerFixture
    ) -> None:
        """Test that when both metrics fail and the operation also fails,
        the original operation exception propagates."""
        mock_observer = MagicMock()
        mmap_error = ValueError("mmap slice assignment is wrong size")
        mock_observer.observe_layer_operation_triggered.side_effect = mmap_error
        mock_observer.observe_layer_operation.side_effect = mmap_error
        mocker.patch(
            "ai.backend.common.resilience.policies.metrics.LayerMetricObserver.instance",
            return_value=mock_observer,
        )

        metric_policy = MetricPolicy(
            MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)
        )

        @Resilience(policies=[metric_policy]).apply()
        async def failing_operation() -> str:
            raise RuntimeError("connection lost")

        with pytest.raises(RuntimeError, match="connection lost"):
            await failing_operation()
