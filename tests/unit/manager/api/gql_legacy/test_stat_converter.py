import uuid
from collections.abc import Mapping
from typing import cast

import pytest

from ai.backend.common.clients.prometheus.metric_types import (
    KernelLiveStatBatchResult,
    KernelLiveStatValues,
)
from ai.backend.common.metrics.types import CAPACITY_SENTINEL
from ai.backend.common.types import KernelId
from ai.backend.common.types import MetricValue as LegacyMetricValue
from ai.backend.manager.api.gql_legacy.stat_converter import LegacyLiveStatConverter


@pytest.fixture
def kernel_id() -> KernelId:
    return KernelId(uuid.uuid4())


@pytest.fixture
def two_kernel_ids() -> tuple[KernelId, KernelId]:
    return KernelId(uuid.uuid4()), KernelId(uuid.uuid4())


def _wrap(by_kernel: Mapping[KernelId, KernelLiveStatValues]) -> KernelLiveStatBatchResult:
    return KernelLiveStatBatchResult(by_kernel=dict(by_kernel))


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
    def test_kernel_with_no_samples_yields_none(self, kernel_id: KernelId) -> None:
        raw = KernelLiveStatBatchResult.empty([kernel_id])
        assert LegacyLiveStatConverter.convert([kernel_id], raw) == {kernel_id: None}


class TestGaugeMetric:
    @pytest.fixture
    def gauge_raw(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _wrap({
            kernel_id: KernelLiveStatValues(
                instant_current={"mem": "1024"},
                instant_capacity={"mem": "8192"},
            )
        })

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("current", "1024"),
            ("capacity", "8192"),
            ("pct", "12.50"),
            ("unit_hint", "bytes"),
        ],
    )
    def test_legacy_field_is_populated(
        self,
        kernel_id: KernelId,
        gauge_raw: KernelLiveStatBatchResult,
        field: str,
        expected: str,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert([kernel_id], gauge_raw), kernel_id)
        assert per_metric["mem"][field] == expected


class TestRateMetric:
    """For a RATE_STAT_METRICS entry the rate-of-change sample is what the
    WebUI expects in `current` and `stats.rate`.
    """

    @pytest.fixture
    def rate_raw(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _wrap({
            kernel_id: KernelLiveStatValues(rate_current={"net_rx": "2048"}),
        })

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("current", "2048"),
            ("stats.rate", "2048"),
            ("unit_hint", "bps"),
        ],
    )
    def test_legacy_field_is_populated(
        self,
        kernel_id: KernelId,
        rate_raw: KernelLiveStatBatchResult,
        field: str,
        expected: str,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert([kernel_id], rate_raw), kernel_id)
        assert per_metric["net_rx"][field] == expected


class TestDiffMetric:
    """For a DIFF_STAT_METRICS entry the rate-converted sample feeds `current`
    and is mirrored to `stats.diff`.
    """

    @pytest.fixture
    def diff_raw(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _wrap({
            kernel_id: KernelLiveStatValues(
                rate_current={"cpu_util": "150"},
                instant_capacity={"cpu_util": "1000"},
            ),
        })

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("current", "150"),
            ("pct", "15.00"),
            ("stats.diff", "150"),
        ],
    )
    def test_legacy_field_is_populated(
        self,
        kernel_id: KernelId,
        diff_raw: KernelLiveStatBatchResult,
        field: str,
        expected: str,
    ) -> None:
        per_metric = _per_metric(LegacyLiveStatConverter.convert([kernel_id], diff_raw), kernel_id)
        assert per_metric["cpu_util"][field] == expected


class TestPctDerivation:
    @pytest.fixture
    def gauge_with_capacity(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _wrap({
            kernel_id: KernelLiveStatValues(
                instant_current={"mem": "200"},
                instant_capacity={"mem": "800"},
            ),
        })

    def test_pct_is_computed_from_current_and_capacity(
        self,
        kernel_id: KernelId,
        gauge_with_capacity: KernelLiveStatBatchResult,
    ) -> None:
        per_metric = _per_metric(
            LegacyLiveStatConverter.convert([kernel_id], gauge_with_capacity), kernel_id
        )
        assert per_metric["mem"]["pct"] == "25.00"


class TestDerivedStats:
    def test_maps_derived_value_types_to_legacy_stats_fields(
        self,
        kernel_id: KernelId,
    ) -> None:
        raw = _wrap({
            kernel_id: KernelLiveStatValues(
                instant_current={"mem": "200"},
                max={"mem": "300"},
                avg={"mem": "250"},
            ),
        })

        per_metric = _per_metric(LegacyLiveStatConverter.convert([kernel_id], raw), kernel_id)

        assert per_metric["mem"]["stats.max"] == "300"
        assert per_metric["mem"]["stats.avg"] == "250"


class TestCapacityDefault:
    """For metrics not in CAPACITY_SENTINEL_METRICS, capacity defaults to "0"
    when the Prometheus pipeline emits no CAPACITY sample.
    """

    @pytest.fixture
    def gauge_no_capacity(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _wrap({
            kernel_id: KernelLiveStatValues(instant_current={"io_scratch_size": "0"}),
        })

    def test_capacity_defaults_to_zero_string(
        self,
        kernel_id: KernelId,
        gauge_no_capacity: KernelLiveStatBatchResult,
    ) -> None:
        per_metric = _per_metric(
            LegacyLiveStatConverter.convert([kernel_id], gauge_no_capacity), kernel_id
        )
        assert per_metric["io_scratch_size"]["capacity"] == "0"


class TestCapacitySentinel:
    """Unbounded metrics (cpu_used / net_rx / net_tx / io_read / io_write)
    get a synthesized capacity sentinel when the Prometheus pipeline emits no
    CAPACITY sample, preserving the BA-5806 invariant for legacy consumers.
    """

    @pytest.fixture
    def sentinel_raw(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _wrap({
            kernel_id: KernelLiveStatValues(instant_current={"io_read": "0"}),
        })

    def test_capacity_is_sentinel_for_unbounded_metric(
        self,
        kernel_id: KernelId,
        sentinel_raw: KernelLiveStatBatchResult,
    ) -> None:
        per_metric = _per_metric(
            LegacyLiveStatConverter.convert([kernel_id], sentinel_raw), kernel_id
        )
        assert per_metric["io_read"]["capacity"] == CAPACITY_SENTINEL

    @pytest.fixture
    def sentinel_raw_with_reported_capacity(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _wrap({
            kernel_id: KernelLiveStatValues(
                instant_current={"net_rx": "0"},
                instant_capacity={"net_rx": "9999"},
            ),
        })

    def test_sentinel_overrides_reported_capacity(
        self,
        kernel_id: KernelId,
        sentinel_raw_with_reported_capacity: KernelLiveStatBatchResult,
    ) -> None:
        """Agent may emit a bogus capacity sample for unbounded metrics
        (initialized via `measure.value`); the converter must overwrite it
        with the sentinel rather than preserve the meaningless value."""
        per_metric = _per_metric(
            LegacyLiveStatConverter.convert([kernel_id], sentinel_raw_with_reported_capacity),
            kernel_id,
        )
        assert per_metric["net_rx"]["capacity"] == CAPACITY_SENTINEL


class TestUnknownMetric:
    """An unregistered metric falls back to its own name as the unit_hint
    so the sample is not dropped and the missing registration is
    self-evident in the response payload.
    """

    @pytest.fixture
    def unknown_metric_raw(self, kernel_id: KernelId) -> KernelLiveStatBatchResult:
        return _wrap({
            kernel_id: KernelLiveStatValues(instant_current={"brand_new_metric": "1"}),
        })

    def test_unknown_metric_uses_name_as_unit_hint(
        self,
        kernel_id: KernelId,
        unknown_metric_raw: KernelLiveStatBatchResult,
    ) -> None:
        per_metric = _per_metric(
            LegacyLiveStatConverter.convert([kernel_id], unknown_metric_raw), kernel_id
        )
        assert per_metric["brand_new_metric"]["unit_hint"] == "brand_new_metric"
        assert per_metric["brand_new_metric"]["current"] == "1"


class TestMultiKernelIsolation:
    @pytest.fixture
    def two_kernel_raw(
        self, two_kernel_ids: tuple[KernelId, KernelId]
    ) -> KernelLiveStatBatchResult:
        a, b = two_kernel_ids
        return _wrap({
            a: KernelLiveStatValues(instant_current={"mem": "10"}),
            b: KernelLiveStatValues(instant_current={"mem": "20"}),
        })

    def test_per_kernel_values_do_not_leak(
        self,
        two_kernel_ids: tuple[KernelId, KernelId],
        two_kernel_raw: KernelLiveStatBatchResult,
    ) -> None:
        a, b = two_kernel_ids
        out = LegacyLiveStatConverter.convert([a, b], two_kernel_raw)
        per_metric_a = _per_metric(out, a)
        per_metric_b = _per_metric(out, b)
        assert per_metric_a["mem"]["current"] == "10"
        assert per_metric_b["mem"]["current"] == "20"
