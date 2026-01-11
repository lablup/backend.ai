"""Test utility functions for agent selectors."""

from __future__ import annotations

from decimal import Decimal

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import AgentInfo
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.utils import (
    count_unutilized_capabilities,
    order_slots_by_priority,
)


class TestUtilityFunctions:
    """Test utility functions used by selectors."""

    def test_count_unutilized_capabilities_no_unused(
        self,
        agent_with_all_resources_utilized: AgentInfo,
    ) -> None:
        """Test counting when all requested resources are used."""
        requested_slots = ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal("4096"),
            "cuda.shares": Decimal("1"),
        })

        count = count_unutilized_capabilities(agent_with_all_resources_utilized, requested_slots)
        assert count == 0

    def test_count_unutilized_capabilities_with_unused(
        self,
        agent_with_unutilized_accelerators: AgentInfo,
    ) -> None:
        """Test counting with some zero-requested resources."""
        requested_slots = ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal("4096"),
            "cuda.shares": Decimal("0"),  # Not requested
            "tpu": Decimal("0"),  # Not requested
        })

        count = count_unutilized_capabilities(agent_with_unutilized_accelerators, requested_slots)
        assert count == 2  # cuda.shares and tpu are unutilized

    def test_count_unutilized_capabilities_unavailable_resources(
        self,
        agent_with_fully_occupied_gpu: AgentInfo,
    ) -> None:
        """Test that unavailable resources are not counted."""
        requested_slots = ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal("4096"),
            "cuda.shares": Decimal("0"),
        })

        count = count_unutilized_capabilities(agent_with_fully_occupied_gpu, requested_slots)
        assert count == 0  # cuda.shares is zero-requested but not available

    def test_order_slots_by_priority_basic(self) -> None:
        """Test basic slot ordering by priority."""
        requested_slots = ResourceSlot({
            "cpu": Decimal("1"),
            "mem": Decimal("2048"),
            "cuda.shares": Decimal("1"),
            "disk": Decimal("10"),
        })
        priority_order = ["mem", "cpu", "cuda.shares"]

        result = order_slots_by_priority(requested_slots, priority_order)
        assert result == ["mem", "cpu", "cuda.shares", "disk"]

    def test_order_slots_by_priority_missing_priorities(self) -> None:
        """Test ordering when some slots are not in priority list."""
        requested_slots = ResourceSlot({
            "cpu": Decimal("1"),
            "mem": Decimal("2048"),
            "special": Decimal("5"),
            "custom": Decimal("3"),
        })
        priority_order = ["cpu"]

        result = order_slots_by_priority(requested_slots, priority_order)
        assert result[0] == "cpu"
        assert set(result[1:]) == {"custom", "mem", "special"}
        # Non-priority slots should be sorted alphabetically
        assert result[1:] == sorted(result[1:])

    def test_order_slots_by_priority_empty_priority(self) -> None:
        """Test ordering with empty priority list."""
        requested_slots = ResourceSlot({
            "zebra": Decimal("1"),
            "alpha": Decimal("2"),
            "beta": Decimal("3"),
        })
        priority_order: list[str] = []

        result = order_slots_by_priority(requested_slots, priority_order)
        assert result == ["alpha", "beta", "zebra"]  # Alphabetical order

    def test_order_slots_by_priority_nonexistent_priorities(self) -> None:
        """Test that non-existent priority slots are ignored."""
        requested_slots = ResourceSlot({
            "cpu": Decimal("1"),
            "mem": Decimal("2048"),
        })
        priority_order = ["gpu", "tpu", "cpu", "mem", "disk"]

        result = order_slots_by_priority(requested_slots, priority_order)
        assert result == ["cpu", "mem"]  # Only requested slots appear

    def test_agent_info_calculations(
        self,
        agent_for_resource_calculation: AgentInfo,
    ) -> None:
        """Test that AgentInfo correctly calculates available resources."""
        free_slots = (
            agent_for_resource_calculation.available_slots
            - agent_for_resource_calculation.occupied_slots
        )
        assert free_slots["cpu"] == Decimal("6")
        assert free_slots["mem"] == Decimal("12288")
