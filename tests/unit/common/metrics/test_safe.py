from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import ai.backend.common.metrics.safe as safe_mod
from ai.backend.common.metrics.safe import (
    SafeCounter,
    SafeGauge,
    SafeHistogram,
    SafeLabeledMetric,
    _NoopLabeledMetric,
    _trip,
    is_metrics_disabled,
    metrics_trip_info,
)


@pytest.fixture(autouse=True)
def _reset_circuit_breaker() -> None:
    """Reset global circuit breaker state before each test."""
    safe_mod._metrics_disabled = False
    safe_mod._error_logged = False
    safe_mod._tripped_at = None
    safe_mod._trip_error_message = None


class TestCircuitBreakerState:
    def test_initially_not_disabled(self) -> None:
        assert is_metrics_disabled() is False

    def test_trip_disables_metrics(self) -> None:
        _trip(ValueError("mmap slice assignment is wrong size"))
        assert is_metrics_disabled() is True

    def test_trip_stores_error_info(self) -> None:
        _trip(ValueError("mmap slice assignment is wrong size"))
        tripped_at, error_msg = metrics_trip_info()
        assert tripped_at is not None
        assert error_msg == "mmap slice assignment is wrong size"

    def test_trip_is_idempotent(self) -> None:
        _trip(ValueError("first error"))
        first_tripped_at, first_msg = metrics_trip_info()
        _trip(ValueError("second error"))
        second_tripped_at, second_msg = metrics_trip_info()
        assert first_tripped_at == second_tripped_at
        assert first_msg == second_msg == "first error"

    def test_trip_logs_warning_once(self) -> None:
        with patch.object(safe_mod, "log") as mock_log:
            _trip(ValueError("error 1"))
            _trip(ValueError("error 2"))
            assert mock_log.warning.call_count == 1


class TestSafeLabeledMetric:
    def test_inc_delegates_to_child(self) -> None:
        child = MagicMock()
        metric = SafeLabeledMetric(child)
        metric.inc(2)
        child.inc.assert_called_once_with(2)

    def test_dec_delegates_to_child(self) -> None:
        child = MagicMock()
        metric = SafeLabeledMetric(child)
        metric.dec(3)
        child.dec.assert_called_once_with(3)

    def test_set_delegates_to_child(self) -> None:
        child = MagicMock()
        metric = SafeLabeledMetric(child)
        metric.set(42.0)
        child.set.assert_called_once_with(42.0)

    def test_observe_delegates_to_child(self) -> None:
        child = MagicMock()
        metric = SafeLabeledMetric(child)
        metric.observe(1.5)
        child.observe.assert_called_once_with(1.5)

    def test_inc_trips_on_valueerror(self) -> None:
        child = MagicMock()
        child.inc.side_effect = ValueError("mmap error")
        metric = SafeLabeledMetric(child)
        metric.inc()
        assert is_metrics_disabled() is True

    def test_noop_after_trip(self) -> None:
        child = MagicMock()
        child.inc.side_effect = ValueError("mmap error")
        metric = SafeLabeledMetric(child)
        metric.inc()  # trips
        child.reset_mock()
        metric.inc()  # should be no-op
        child.inc.assert_not_called()

    def test_observe_trips_on_valueerror(self) -> None:
        child = MagicMock()
        child.observe.side_effect = ValueError("mmap error")
        metric = SafeLabeledMetric(child)
        metric.observe(1.0)
        assert is_metrics_disabled() is True

    def test_other_exceptions_propagate(self) -> None:
        child = MagicMock()
        child.inc.side_effect = TypeError("unexpected")
        metric = SafeLabeledMetric(child)
        with pytest.raises(TypeError, match="unexpected"):
            metric.inc()
        assert is_metrics_disabled() is False


class TestNoopLabeledMetric:
    def test_all_methods_are_noop(self) -> None:
        noop = _NoopLabeledMetric()
        noop.inc()
        noop.dec()
        noop.set(0)
        noop.observe(0)


class TestSafeCounter:
    def test_labels_returns_safe_labeled(self) -> None:
        counter = SafeCounter(
            name="test_counter",
            documentation="test",
            labelnames=["a"],
        )
        result = counter.labels(a="x")
        assert isinstance(result, SafeLabeledMetric)

    def test_labels_returns_noop_after_trip(self) -> None:
        _trip(ValueError("broken"))
        counter = SafeCounter(
            name="test_counter_tripped",
            documentation="test",
            labelnames=["a"],
        )
        result = counter.labels(a="x")
        assert isinstance(result, _NoopLabeledMetric)

    def test_labels_catches_valueerror(self) -> None:
        counter = SafeCounter(
            name="test_counter_err",
            documentation="test",
            labelnames=["a"],
        )
        with patch.object(
            type(counter).__bases__[0], "labels", side_effect=ValueError("mmap error")
        ):
            result = counter.labels(a="x")
            assert isinstance(result, _NoopLabeledMetric)
            assert is_metrics_disabled() is True

    def test_direct_inc_catches_valueerror(self) -> None:
        counter = SafeCounter(
            name="test_counter_direct",
            documentation="test",
        )
        with patch.object(type(counter).__bases__[0], "inc", side_effect=ValueError("mmap error")):
            counter.inc()
            assert is_metrics_disabled() is True

    def test_direct_inc_noop_after_trip(self) -> None:
        _trip(ValueError("broken"))
        counter = SafeCounter(
            name="test_counter_noop",
            documentation="test",
        )
        # Should not raise
        counter.inc()


class TestSafeGauge:
    def test_direct_set_catches_valueerror(self) -> None:
        gauge = SafeGauge(
            name="test_gauge_set",
            documentation="test",
            multiprocess_mode="livesum",
        )
        with patch.object(type(gauge).__bases__[0], "set", side_effect=ValueError("mmap error")):
            gauge.set(42.0)
            assert is_metrics_disabled() is True

    def test_direct_inc_dec_noop_after_trip(self) -> None:
        _trip(ValueError("broken"))
        gauge = SafeGauge(
            name="test_gauge_noop",
            documentation="test",
            multiprocess_mode="livesum",
        )
        gauge.inc()
        gauge.dec()
        gauge.set(0)


class TestSafeHistogram:
    def test_direct_observe_catches_valueerror(self) -> None:
        histogram = SafeHistogram(
            name="test_histogram_obs",
            documentation="test",
        )
        with patch.object(
            type(histogram).__bases__[0], "observe", side_effect=ValueError("mmap error")
        ):
            histogram.observe(1.0)
            assert is_metrics_disabled() is True

    def test_direct_observe_noop_after_trip(self) -> None:
        _trip(ValueError("broken"))
        histogram = SafeHistogram(
            name="test_histogram_noop",
            documentation="test",
        )
        histogram.observe(1.0)
