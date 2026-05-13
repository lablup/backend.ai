import uuid
from collections.abc import Mapping, Sequence
from typing import cast

import pytest

from ai.backend.common.clients.prometheus.metric_types import KernelLiveStatBatchResult
from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.types import KernelId
from ai.backend.common.types import MetricValue as LegacyMetricValue
from ai.backend.manager.api.gql_legacy.stat_converter import LegacyLiveStatConverter


@pytest.fixture
def kernel_id() -> KernelId:
    return KernelId(uuid.uuid4())


@pytest.fixture
def two_kernel_ids() -> tuple[KernelId, KernelId]:
    return KernelId(uuid.uuid4()), KernelId(uuid.uuid4())


def _build_result(
    samples_by_kernel: Mapping[KernelId, Sequence[MetricValue]],
) -> KernelLiveStatBatchResult:
    return KernelLiveStatBatchResult.from_metric_values(
        list(samples_by_kernel.keys()),
        {k: list(v) for k, v in samples_by_kernel.items()},
    )


def _per_metric(
    out: Mapping[KernelId, dict[str, LegacyMetricValue] | None], kernel_id: KernelId
) -> Mapping[str, Mapping[str, object]]:
    """Narrow the converter result to a non-Optional, dynamically-indexable
    view so that parametrized tests can assert against arbitrary
    `(metric_name, field)` pairs without violating TypedDict literal-key
    rules.
    """
    per_kernel = out[kernel_id]
    assert per_kernel is not None
    return cast(Mapping[str, Mapping[str, object]], per_kernel)


class TestEmptyKernel:
    @pytest.fixture
    def empty_result(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return KernelLiveStatBatchResult.empty([kernel_id])

    def test_kernel_with_no_samples_yields_none(
        self,
        kernel_id: KernelId,
        empty_result: KernelLiveStatBatchResult,
    ) -> None:
        assert LegacyLiveStatConverter.convert(empty_result) == {kernel_id: None}


class TestGaugeMetric:
    @pytest.fixture
    def gauge_result(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _build_result({
            kernel_id: [
                MetricValue("mem", ValueType.CURRENT, "1024"),
                MetricValue("mem", ValueType.CAPACITY, "8192"),
                MetricValue("mem", ValueType.PCT, "12.5"),
            ]
        })

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("current", "1024"),
            ("capacity", "8192"),
            ("pct", "12.5"),
            ("unit_hint", "bytes"),
        ],
    )
    def test_legacy_field_is_populated(
        self,
        kernel_id: KernelId,
        gauge_result: KernelLiveStatBatchResult,
        field: str,
        expected: str,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert(gauge_result), kernel_id)
        assert per_metric["mem"][field] == expected


class TestRateMetric:
    """For a RATE_STAT_METRICS entry the rate-of-change sample (currents[-1])
    is what the WebUI expects in `current` (legacy Valkey behavior). The
    cumulative gauge (currents[0]) is discarded because the WebUI never
    consumed it on the Valkey path. `stats.rate` is hack-multiplied by
    `UTILIZATION_METRIC_INTERVAL` to recover the per-second magnitude that
    legacy `MovingStatistics.rate` produced (the rate query template applies
    `/ UTILIZATION_METRIC_INTERVAL` so its `current` matches the per-window
    legacy magnitude; the converter undoes that scaling for `stats.rate`).
    """

    @pytest.fixture
    def rate_result(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _build_result({
            kernel_id: [
                MetricValue("net_rx", ValueType.CURRENT, "1000000"),
                MetricValue("net_rx", ValueType.CURRENT, "2048"),
            ]
        })

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("current", "2048"),
            ("stats.rate", "10240.000000"),
            ("unit_hint", "bps"),
        ],
    )
    def test_legacy_field_is_populated(
        self,
        kernel_id: KernelId,
        rate_result: KernelLiveStatBatchResult,
        field: str,
        expected: str,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert(rate_result), kernel_id)
        assert per_metric["net_rx"][field] == expected


class TestDiffMetric:
    """For a DIFF_STAT_METRICS entry the diff-over-window sample (currents[-1])
    is exposed as `current` (legacy Valkey behavior) and mirrored to
    `stats.diff`. The cumulative gauge (currents[0]) is dropped
    """

    @pytest.fixture
    def diff_result(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _build_result({
            kernel_id: [
                MetricValue("cpu_util", ValueType.CURRENT, "5000000"),
                MetricValue("cpu_util", ValueType.PCT, "37.0"),
                MetricValue("cpu_util", ValueType.CURRENT, "150"),
            ]
        })

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("current", "150"),
            ("pct", "37.0"),
            ("stats.diff", "150"),
        ],
    )
    def test_legacy_field_is_populated(
        self,
        kernel_id: KernelId,
        diff_result: KernelLiveStatBatchResult,
        field: str,
        expected: str,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert(diff_result), kernel_id)
        assert per_metric["cpu_util"][field] == expected


class TestWindowStats:
    """MAX/AVG samples from `_build_window_stats_preset` and RATE samples
    from `_build_rate_stats_preset` flow into the legacy `stats.max`,
    `stats.avg`, and `stats.rate` fields. Without these mappings the
    placeholder `"0"` reaches the GraphQL response unchanged.
    """

    @pytest.fixture
    def window_stats_result(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _build_result({
            kernel_id: [
                MetricValue("mem", ValueType.CURRENT, "1024"),
                MetricValue("mem", ValueType.MAX, "4096"),
                MetricValue("mem", ValueType.AVG, "2048"),
            ]
        })

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("stats.max", "4096"),
            ("stats.avg", "2048"),
        ],
    )
    def test_window_stats_are_populated(
        self,
        kernel_id: KernelId,
        window_stats_result: KernelLiveStatBatchResult,
        field: str,
        expected: str,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert(window_stats_result), kernel_id)
        assert per_metric["mem"][field] == expected

    def test_rate_sample_populates_stats_rate_for_counter_rate_metric(
        self,
        kernel_id: KernelId,
    ) -> None:
        # io_read is in STATS_RATE_COUNTER_METRICS — RATE sample is exposed
        # directly without the net_rx/net_tx hack-multiply path.
        result = _build_result({
            kernel_id: [
                MetricValue("io_read", ValueType.CURRENT, "5000"),
                MetricValue("io_read", ValueType.RATE, "120.5"),
            ]
        })
        per_metric = _per_metric(LegacyLiveStatConverter.convert(result), kernel_id)
        assert per_metric["io_read"]["stats.rate"] == "120.5"


class TestPctDerivation:
    """When the Prometheus pipeline does not emit a PCT sample, the converter
    derives the percentage from current/capacity, matching the value the
    Valkey baseline produced via the agent's MovingStatistics.
    """

    @pytest.fixture
    def gauge_with_capacity(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _build_result({
            kernel_id: [
                MetricValue("mem", ValueType.CURRENT, "200"),
                MetricValue("mem", ValueType.CAPACITY, "800"),
            ]
        })

    def test_pct_is_computed_from_current_and_capacity(
        self,
        kernel_id: KernelId,
        gauge_with_capacity: KernelLiveStatBatchResult,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert(gauge_with_capacity), kernel_id)
        assert per_metric["mem"]["pct"] == "25.00"

    def test_explicit_pct_sample_wins_over_derivation(
        self,
        kernel_id: KernelId,
    ) -> None:
        result = _build_result({
            kernel_id: [
                MetricValue("mem", ValueType.CURRENT, "200"),
                MetricValue("mem", ValueType.CAPACITY, "800"),
                MetricValue("mem", ValueType.PCT, "30.0"),
            ]
        })
        per_metric = _per_metric(LegacyLiveStatConverter.convert(result), kernel_id)
        assert per_metric["mem"]["pct"] == "30.0"


class TestCapacityDefault:
    """The legacy Valkey shape always carried a string `capacity`. The
    converter mirrors that — when the Prometheus pipeline emits no CAPACITY
    sample, capacity stays at the `"0"` default rather than `null`.
    """

    @pytest.fixture
    def gauge_no_capacity(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _build_result({kernel_id: [MetricValue("io_read", ValueType.CURRENT, "0")]})

    def test_capacity_defaults_to_zero_string(
        self,
        kernel_id: KernelId,
        gauge_no_capacity: KernelLiveStatBatchResult,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert(gauge_no_capacity), kernel_id)
        assert per_metric["io_read"]["capacity"] == "0"


class TestUnknownMetric:
    """An unregistered metric falls back to its own name as the unit_hint
    so the sample is not dropped and the missing registration is
    self-evident in the response payload.
    """

    @pytest.fixture
    def unknown_metric_result(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _build_result({kernel_id: [MetricValue("brand_new_metric", ValueType.CURRENT, "1")]})

    def test_unknown_metric_uses_name_as_unit_hint(
        self,
        kernel_id: KernelId,
        unknown_metric_result: KernelLiveStatBatchResult,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert(unknown_metric_result), kernel_id)
        assert per_metric["brand_new_metric"]["unit_hint"] == "brand_new_metric"
        assert per_metric["brand_new_metric"]["current"] == "1"


class TestMultiKernelIsolation:
    @pytest.fixture
    def two_kernel_result(
        self, two_kernel_ids: tuple[KernelId, KernelId]
    ) -> KernelLiveStatBatchResult:
        a, b = two_kernel_ids
        return _build_result({
            a: [MetricValue("mem", ValueType.CURRENT, "10")],
            b: [MetricValue("mem", ValueType.CURRENT, "20")],
        })

    def test_per_kernel_values_do_not_leak(
        self,
        two_kernel_ids: tuple[KernelId, KernelId],
        two_kernel_result: KernelLiveStatBatchResult,
    ) -> None:
        a, b = two_kernel_ids
        out = LegacyLiveStatConverter.convert(two_kernel_result)
        per_metric_a = _per_metric(out, a)
        per_metric_b = _per_metric(out, b)
        assert per_metric_a["mem"]["current"] == "10"
        assert per_metric_b["mem"]["current"] == "20"
