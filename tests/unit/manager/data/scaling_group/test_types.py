from __future__ import annotations

from datetime import timedelta

from ai.backend.common.types import AgentSelectionStrategy, SessionTypes
from ai.backend.manager.data.scaling_group.types import ScalingGroupSchedulerOptions


class TestScalingGroupSchedulerOptions:
    """Tests for ScalingGroupSchedulerOptions.to_json method."""

    def test_to_json_converts_all_fields_correctly(self) -> None:
        """Test to_json converts all scheduler options fields correctly."""
        options = ScalingGroupSchedulerOptions(
            allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
            pending_timeout=timedelta(seconds=300),
            config={"key": "value"},
            agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
            agent_selector_config={"selector_key": "selector_value"},
            enforce_spreading_endpoint_replica=True,
            allow_fractional_resource_fragmentation=False,
            route_cleanup_target_statuses=["terminated", "cancelled"],
        )

        result = options.to_json()

        assert result["allowed_session_types"] == ["interactive", "batch"]
        assert result["pending_timeout"] == 300.0
        assert result["config"] == {"key": "value"}
        assert result["agent_selection_strategy"] == "dispersed"
        assert result["agent_selector_config"] == {"selector_key": "selector_value"}
        assert result["enforce_spreading_endpoint_replica"] is True
        assert result["allow_fractional_resource_fragmentation"] is False
        assert result["route_cleanup_target_statuses"] == ["terminated", "cancelled"]

    def test_to_json_handles_empty_collections(self) -> None:
        """Test to_json handles empty lists and dicts."""
        options = ScalingGroupSchedulerOptions(
            allowed_session_types=[],
            pending_timeout=timedelta(minutes=5),
            config={},
            agent_selection_strategy=AgentSelectionStrategy.CONCENTRATED,
            agent_selector_config={},
            enforce_spreading_endpoint_replica=False,
            allow_fractional_resource_fragmentation=True,
            route_cleanup_target_statuses=[],
        )

        result = options.to_json()

        assert result["allowed_session_types"] == []
        assert result["config"] == {}
        assert result["agent_selector_config"] == {}
        assert result["route_cleanup_target_statuses"] == []

    def test_to_json_handles_nested_config(self) -> None:
        """Test to_json handles nested config dictionaries."""
        options = ScalingGroupSchedulerOptions(
            allowed_session_types=[SessionTypes.INTERACTIVE],
            pending_timeout=timedelta(seconds=120),
            config={"level1": {"level2": {"value": 123}}, "list_value": [1, 2, 3]},
            agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
            agent_selector_config={"nested": {"key": "value"}},
            enforce_spreading_endpoint_replica=True,
            allow_fractional_resource_fragmentation=True,
            route_cleanup_target_statuses=["error"],
        )

        result = options.to_json()

        assert result["config"]["level1"]["level2"]["value"] == 123
        assert result["config"]["list_value"] == [1, 2, 3]
        assert result["agent_selector_config"]["nested"]["key"] == "value"
