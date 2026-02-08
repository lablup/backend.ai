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

    # ===== PARAMETRIZED TEST GROUP 2: Clamping Logic Scenarios =====
    @pytest.mark.parametrize(
        "input_data,expected_current,expected_pct",
        [
            # 4 cores, capacity 50, current 300 → clamped to 200
            pytest.param(
                {
                    "node": {"cpu_util": {"current": "300", "capacity": "50"}},
                    "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}, "cpu2": {}, "cpu3": {}}},
                },
                "200",
                None,
                id="4_cores_capacity_50",
            ),
            # 4 cores, capacity 100, current 500 → clamped to 400
            pytest.param(
                {
                    "node": {"cpu_util": {"current": "500", "capacity": "100"}},
                    "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}, "cpu2": {}, "cpu3": {}}},
                },
                "400",
                None,
                id="4_cores_capacity_100",
            ),
            # 4 cores with decimal precision
            pytest.param(
                {
                    "node": {
                        "cpu_util": {"current": "450.5", "capacity": "100.25", "pct": "425.75"}
                    },
                    "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}, "cpu2": {}, "cpu3": {}}},
                },
                "401.00",
                "400",
                id="decimal_precision",
            ),
            # 2 cores, current and pct both need clamping
            pytest.param(
                {
                    "node": {"cpu_util": {"current": "500", "capacity": "100", "pct": "500"}},
                    "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}}},
                },
                "200",
                "200",
                id="2_cores_both_fields_clamped",
            ),
        ],
    )
    async def test_clamping_various_scenarios(
        self,
        input_data: dict[str, Any],
        expected_current: str,
        expected_pct: str | None,
    ) -> None:
        """Test clamping with various core counts, capacity values, and precision."""
        result = clamp_agent_cpu_util(input_data)

        assert result is not None
        assert result["node"]["cpu_util"]["current"] == expected_current
        if expected_pct is not None:
            assert result["node"]["cpu_util"]["pct"] == expected_pct

    @pytest.mark.parametrize(
        "input_data,unchanged_field,unchanged_value",
        [
            pytest.param(
                {
                    "node": {"cpu_util": {"pct": "invalid"}},
                    "devices": {"cpu_util": {"cpu0": {}}},
                },
                "pct",
                "invalid",
                id="invalid_pct_string",
            ),
            pytest.param(
                {
                    "node": {"cpu_util": {"pct": "abc123"}},
                    "devices": {"cpu_util": {"cpu0": {}}},
                },
                "pct",
                "abc123",
                id="alphanumeric_pct",
            ),
            pytest.param(
                {
                    "node": {"cpu_util": {"current": "not_a_number", "capacity": "100"}},
                    "devices": {"cpu_util": {"cpu0": {}}},
                },
                "current",
                "not_a_number",
                id="invalid_current_string",
            ),
            pytest.param(
                {
                    "node": {"cpu_util": {"current": "500", "capacity": "invalid"}},
                    "devices": {"cpu_util": {"cpu0": {}}},
                },
                "current",
                "500",
                id="invalid_capacity_string",
            ),
        ],
    )
    async def test_invalid_decimal_values_handled_gracefully(
        self,
        input_data: dict[str, Any],
        unchanged_field: str,
        unchanged_value: str,
    ) -> None:
        """Test that invalid decimal strings are handled gracefully without raising."""
        result = clamp_agent_cpu_util(input_data)

        assert result is not None
        assert result["node"]["cpu_util"][unchanged_field] == unchanged_value
