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
            {"node": {"cpu_util": {"current": 200}}},
            {"node": {"cpu_util": {"current": 200}}, "devices": {}},
            {"node": {"cpu_util": {"current": 200}}, "devices": {"cpu_util": {}}},
        ],
    )
    async def test_edge_cases_no_clamping(self, input_data: dict[str, Any] | None) -> None:
        """Test edge cases where no clamping should occur."""
        result = clamp_agent_cpu_util(input_data)
        assert result == input_data

    # ===== PARAMETRIZED TEST GROUP 2: Clamping Behavior =====
    @pytest.mark.parametrize(
        "num_cores,node_data,expected_node_data",
        [
            # Clamp current only
            (4, {"current": 500, "pct": 300}, {"current": 400, "pct": 300}),
            # Clamp pct only
            (4, {"current": 300, "pct": 450}, {"current": 300, "pct": 400}),
            # Clamp both fields
            (4, {"current": 500, "pct": 600}, {"current": 400, "pct": 400}),
        ],
    )
    async def test_clamping_behavior(
        self,
        num_cores: int,
        node_data: dict[str, Any],
        expected_node_data: dict[str, Any],
    ) -> None:
        """Test various clamping scenarios."""
        stat_data = {
            "node": {"cpu_util": node_data.copy()},
            "devices": {"cpu_util": {f"cpu{i}": {} for i in range(num_cores)}},
        }

        result = clamp_agent_cpu_util(stat_data)

        assert result is not None
        assert result is stat_data  # In-place mutation
        assert result["node"]["cpu_util"] == expected_node_data

    # ===== PARAMETRIZED TEST GROUP 3: Different Core Counts =====
    @pytest.mark.parametrize(
        "num_cores,cpu_value",
        [
            (1, 150),
            (4, 500),
            (16, 2000),
            (32, 4000),
        ],
    )
    async def test_different_core_counts(
        self,
        num_cores: int,
        cpu_value: float,
    ) -> None:
        """Test clamping with various CPU core counts."""
        stat_data = {
            "node": {"cpu_util": {"current": cpu_value}},
            "devices": {"cpu_util": {f"cpu{i}": {} for i in range(num_cores)}},
        }

        result = clamp_agent_cpu_util(stat_data)

        assert result is not None
        expected_max = num_cores * 100
        assert result["node"]["cpu_util"]["current"] == expected_max

    @pytest.fixture
    async def stat_data_with_extra_fields(self) -> dict[str, Any]:
        """Fixture providing stat_data with extra fields in cpu_util."""
        return {
            "node": {
                "cpu_util": {
                    "current": 500,
                    "pct": 500,
                    "extra_field": 999,
                }
            },
            "devices": {"cpu_util": {"cpu0": {}, "cpu1": {}}},
        }

    async def test_handles_extra_fields_in_cpu_util(
        self, stat_data_with_extra_fields: dict[str, Any]
    ) -> None:
        """Test that extra fields in cpu_util are preserved and not clamped."""
        result = clamp_agent_cpu_util(stat_data_with_extra_fields)

        assert result is not None
        assert result["node"]["cpu_util"]["current"] == 200
        assert result["node"]["cpu_util"]["pct"] == 200
        assert result["node"]["cpu_util"]["extra_field"] == 999  # Not clamped
