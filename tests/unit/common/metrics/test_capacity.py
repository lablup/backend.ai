from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.metrics.types import (
    CAPACITY_SENTINEL,
    KernelLiveStatValues,
)
from ai.backend.common.types import KernelId


def _capacities_of(result: KernelLiveStatValues, kernel_id: KernelId) -> dict[str, str]:
    """Return `{metric_name: value}` for every CAPACITY sample of `kernel_id`."""
    return {
        v.metric_name: v.value
        for v in result.values_by_kernel[kernel_id]
        if v.value_type is ValueType.CAPACITY
    }


class TestWithCapacitySentinels:
    """Tests for `KernelLiveStatValues.with_capacity_sentinels`."""

    @pytest.fixture()
    def kernel_id(self) -> KernelId:
        return KernelId(UUID("12345678-1234-5678-1234-567812345678"))

    @pytest.fixture()
    def other_kernel_id(self) -> KernelId:
        return KernelId(UUID("87654321-4321-8765-4321-876543218765"))

    @pytest.mark.parametrize(
        "metric_name",
        ["cpu_used", "net_rx", "net_tx", "io_read", "io_write"],
    )
    async def test_appends_sentinel_capacity_for_whitelisted_live_metric(
        self, kernel_id: KernelId, metric_name: str
    ) -> None:
        """Whitelisted metrics with a CURRENT sample but no CAPACITY sample
        receive a synthetic capacity carrying `CAPACITY_SENTINEL`.
        """
        result = KernelLiveStatValues.with_capacity_sentinels({
            kernel_id: [MetricValue(metric_name, ValueType.CURRENT, "42")],
        })
        assert _capacities_of(result, kernel_id) == {metric_name: CAPACITY_SENTINEL}

    async def test_existing_capacity_is_preserved(self, kernel_id: KernelId) -> None:
        """A real Prometheus capacity sample is not overwritten by the sentinel."""
        result = KernelLiveStatValues.with_capacity_sentinels({
            kernel_id: [
                MetricValue("net_rx", ValueType.CURRENT, "10"),
                MetricValue("net_rx", ValueType.CAPACITY, "999"),
            ],
        })
        assert _capacities_of(result, kernel_id) == {"net_rx": "999"}

    async def test_skips_metric_without_current_sample(self, kernel_id: KernelId) -> None:
        """No phantom capacity is added when the metric has no CURRENT sample."""
        result = KernelLiveStatValues.with_capacity_sentinels({kernel_id: []})
        assert _capacities_of(result, kernel_id) == {}

    @pytest.mark.parametrize("metric_name", ["mem", "io_scratch_size", "cpu_util"])
    async def test_metric_outside_whitelist_is_untouched(
        self, kernel_id: KernelId, metric_name: str
    ) -> None:
        """Metrics that have a real Prometheus capacity series are left alone."""
        result = KernelLiveStatValues.with_capacity_sentinels({
            kernel_id: [MetricValue(metric_name, ValueType.CURRENT, "1")],
        })
        assert _capacities_of(result, kernel_id) == {}

    async def test_isolates_per_kernel(
        self, kernel_id: KernelId, other_kernel_id: KernelId
    ) -> None:
        """Sentinel injection on one kernel does not leak into another."""
        result = KernelLiveStatValues.with_capacity_sentinels({
            kernel_id: [MetricValue("net_rx", ValueType.CURRENT, "1")],
            other_kernel_id: [MetricValue("mem", ValueType.CURRENT, "2")],
        })
        assert _capacities_of(result, kernel_id) == {"net_rx": CAPACITY_SENTINEL}
        assert _capacities_of(result, other_kernel_id) == {}

    async def test_input_is_not_mutated(self, kernel_id: KernelId) -> None:
        """The caller's input list is left untouched."""
        original = [MetricValue("net_rx", ValueType.CURRENT, "1")]
        KernelLiveStatValues.with_capacity_sentinels({kernel_id: original})
        assert original == [MetricValue("net_rx", ValueType.CURRENT, "1")]
