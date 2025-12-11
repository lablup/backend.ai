from collections.abc import Callable
from typing import Any

import pytest

from ai.backend.manager.stat_utils import clamp_agent_cpu_util


class TestClampAgentCpuUtil:
    """Tests for the clamp_agent_cpu_util utility function."""

    # ===== PARAMETRIZED TEST GROUP 1: Edge Cases =====
    @pytest.mark.parametrize(
        "input_data",
        [
            None,
            {},
            {"devices": {"cpu_util": {"cpu0": {}}}},
            {"node": {}, "devices": {"cpu_util": {"cpu0": {}}}},
            {"node": {"cpu_util": {"current": "200"}}},
            {"node": {"cpu_util": {"current": "200"}}, "devices": {}},
            {"node": {"cpu_util": {"current": "200"}}, "devices": {"cpu_util": {}}},
        ],
    )
    async def test_edge_cases_no_clamping(self, input_data: dict[str, Any] | None) -> None:
        """Test edge cases where no clamping should occur."""
        result = clamp_agent_cpu_util(input_data)
        assert result == input_data

    # ===== Factory fixture for parametrized tests =====
    @pytest.fixture
    def make_stat_data(self) -> Callable[..., dict[str, Any]]:
        """Factory fixture to create stat_data with given parameters."""

        def _make(
            num_cores: int,
            pct: str | None = None,
            current: str | None = None,
            capacity: str | None = None,
            **extra_fields: Any,
        ) -> dict[str, Any]:
            cpu_util: dict[str, Any] = {}
            if pct is not None:
                cpu_util["pct"] = pct
            if current is not None:
                cpu_util["current"] = current
            if capacity is not None:
                cpu_util["capacity"] = capacity
            cpu_util.update(extra_fields)

            return {
                "node": {"cpu_util": cpu_util},
                "devices": {"cpu_util": {f"cpu{i}": {} for i in range(num_cores)}},
            }

        return _make

    # ===== PARAMETRIZED TEST GROUP 2: Clamping pct only =====
    @pytest.mark.parametrize(
        "num_cores,pct_value,expected_pct",
        [
            # Within limit - no clamping
            (4, "300", "300"),
            # Exact limit - no clamping
            (4, "400", "400"),
            # Exceeds limit - clamp
            (4, "450", "400"),
            (4, "600", "400"),
        ],
    )
    async def test_clamping_pct(
        self,
        make_stat_data: Callable[..., dict[str, Any]],
        num_cores: int,
        pct_value: str,
        expected_pct: str,
    ) -> None:
        """Test pct clamping scenarios."""
        stat_data = make_stat_data(num_cores, pct=pct_value)

        result = clamp_agent_cpu_util(stat_data)

        assert result is not None
        assert result is stat_data  # In-place mutation
        assert result["node"]["cpu_util"]["pct"] == expected_pct

    # ===== PARAMETRIZED TEST GROUP 3: Clamping current with capacity =====
    @pytest.mark.parametrize(
        "num_cores,current_value,capacity_value,expected_current",
        [
            # Within limit - no clamping
            (4, "300", "100", "300"),
            # Exact limit - no clamping
            (4, "400", "100", "400"),
            # Exceeds limit - clamp to capacity * num_cores
            (4, "500", "100", "400"),
            (2, "300", "100", "200"),
            (8, "1000", "100", "800"),
        ],
    )
    async def test_clamping_current_with_capacity(
        self,
        make_stat_data: Callable[..., dict[str, Any]],
        num_cores: int,
        current_value: str,
        capacity_value: str,
        expected_current: str,
    ) -> None:
        """Test current clamping with capacity field."""
        stat_data = make_stat_data(num_cores, current=current_value, capacity=capacity_value)

        result = clamp_agent_cpu_util(stat_data)

        assert result is not None
        assert result is stat_data  # In-place mutation
        assert result["node"]["cpu_util"]["current"] == expected_current

    # ===== PARAMETRIZED TEST GROUP 4: Clamping both pct and current =====
    @pytest.mark.parametrize(
        "num_cores,pct_value,current_value,capacity_value,expected_pct,expected_current",
        [
            # Both within limit
            (4, "300", "300", "100", "300", "300"),
            # Clamp pct only
            (4, "450", "300", "100", "400", "300"),
            # Clamp current only
            (4, "300", "500", "100", "300", "400"),
            # Clamp both
            (4, "600", "500", "100", "400", "400"),
        ],
    )
    async def test_clamping_both_fields(
        self,
        make_stat_data: Callable[..., dict[str, Any]],
        num_cores: int,
        pct_value: str,
        current_value: str,
        capacity_value: str,
        expected_pct: str,
        expected_current: str,
    ) -> None:
        """Test clamping both pct and current."""
        stat_data = make_stat_data(
            num_cores, pct=pct_value, current=current_value, capacity=capacity_value
        )

        result = clamp_agent_cpu_util(stat_data)

        assert result is not None
        assert result is stat_data  # In-place mutation
        assert result["node"]["cpu_util"]["pct"] == expected_pct
        assert result["node"]["cpu_util"]["current"] == expected_current

    # ===== INDIVIDUAL TESTS =====
    @pytest.fixture
    def stat_data_4_cores_current_500_no_capacity(self) -> dict[str, Any]:
        """Stat data with current but no capacity - should not clamp."""
        return {
            "node": {"cpu_util": {"current": "500"}},
            "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}, "cpu2": {}, "cpu3": {}}},
        }

    async def test_current_without_capacity_no_clamping(
        self, stat_data_4_cores_current_500_no_capacity: dict[str, Any]
    ) -> None:
        """Test that current is not clamped when capacity is missing."""
        result = clamp_agent_cpu_util(stat_data_4_cores_current_500_no_capacity)

        assert result is not None
        assert result["node"]["cpu_util"]["current"] == "500"  # Not clamped

    @pytest.fixture
    def stat_data_2_cores_with_other_fields(self) -> dict[str, Any]:
        """Stat data with other fields to test preservation during clamping."""
        return {
            "node": {
                "cpu_util": {"current": "500", "capacity": "100", "pct": "500"},
                "mem": {"used": 1000},
            },
            "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}}},
            "other_field": "preserved",
        }

    async def test_preserves_other_fields(
        self, stat_data_2_cores_with_other_fields: dict[str, Any]
    ) -> None:
        """Test that clamping preserves other fields in the data structure."""
        result = clamp_agent_cpu_util(stat_data_2_cores_with_other_fields)

        assert result is not None
        assert result["node"]["mem"] == {"used": 1000}
        assert result["other_field"] == "preserved"
        assert result["node"]["cpu_util"]["current"] == "200"
        assert result["node"]["cpu_util"]["pct"] == "200"

    @pytest.fixture
    def stat_data_4_cores_for_mutation_test(self) -> dict[str, Any]:
        """Stat data to test in-place mutation."""
        return {
            "node": {"cpu_util": {"current": "500", "capacity": "100"}},
            "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}, "cpu2": {}, "cpu3": {}}},
        }

    async def test_in_place_mutation(
        self, stat_data_4_cores_for_mutation_test: dict[str, Any]
    ) -> None:
        """Test that the function mutates the dict in-place."""
        result = clamp_agent_cpu_util(stat_data_4_cores_for_mutation_test)

        assert result is not None
        assert result is stat_data_4_cores_for_mutation_test  # Same object
        assert result["node"]["cpu_util"]["current"] == "400"

    @pytest.fixture
    def stat_data_2_cores_with_extra_fields(self) -> dict[str, Any]:
        """Stat data with extra fields in cpu_util to test preservation."""
        return {
            "node": {
                "cpu_util": {
                    "current": "500",
                    "capacity": "100",
                    "pct": "500",
                    "extra_field": 999,
                }
            },
            "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}}},
        }

    async def test_handles_extra_fields_in_cpu_util(
        self, stat_data_2_cores_with_extra_fields: dict[str, Any]
    ) -> None:
        """Test that extra fields in cpu_util are preserved and not clamped."""
        result = clamp_agent_cpu_util(stat_data_2_cores_with_extra_fields)

        assert result is not None
        assert result["node"]["cpu_util"]["current"] == "200"
        assert result["node"]["cpu_util"]["pct"] == "200"
        assert result["node"]["cpu_util"]["extra_field"] == 999  # Not clamped

    @pytest.fixture
    def stat_data_4_cores_capacity_50(self) -> dict[str, Any]:
        """Stat data with capacity=50 to test different capacity values."""
        return {
            "node": {"cpu_util": {"current": "300", "capacity": "50"}},
            "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}, "cpu2": {}, "cpu3": {}}},
        }

    async def test_different_capacity_values(
        self, stat_data_4_cores_capacity_50: dict[str, Any]
    ) -> None:
        """Test clamping with various capacity values."""
        result = clamp_agent_cpu_util(stat_data_4_cores_capacity_50)

        assert result is not None
        # Capacity 50 * 4 cores = 200 max
        assert result["node"]["cpu_util"]["current"] == "200"

    @pytest.fixture
    def stat_data_4_cores_decimal_precision(self) -> dict[str, Any]:
        """Stat data with decimal values to test precision handling."""
        return {
            "node": {"cpu_util": {"current": "450.5", "capacity": "100.25", "pct": "425.75"}},
            "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}, "cpu2": {}, "cpu3": {}}},
        }

    async def test_decimal_precision(
        self, stat_data_4_cores_decimal_precision: dict[str, Any]
    ) -> None:
        """Test that Decimal handles fractional values correctly."""
        result = clamp_agent_cpu_util(stat_data_4_cores_decimal_precision)

        assert result is not None
        # capacity (100.25) * num_cores (4) = 401.00
        assert result["node"]["cpu_util"]["current"] == "401.00"
        # num_cores (4) * 100 = 400
        assert result["node"]["cpu_util"]["pct"] == "400"
