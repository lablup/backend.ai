"""Tests for agent selection strategy configuration and selection logic.

This test validates the bug fix: ensuring that agent_selection_strategy is correctly
retrieved from ScalingGroupOpts.agent_selection_strategy field (not from config dict)
and the appropriate selector is chosen based on that value.
"""

from __future__ import annotations

import pytest

from ai.backend.common.types import (
    AgentSelectionStrategy,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.base import SchedulingSpec
from ai.backend.manager.repositories.scheduler.types.scaling_group import ScalingGroupMeta
from ai.backend.manager.repositories.scheduler.types.scheduling import SchedulingData
from ai.backend.manager.repositories.scheduler.types.session import PendingSessions
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
    SessionProvisioner,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.legacy import (
    LegacyAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.roundrobin import (
    RoundRobinAgentSelector,
)


@pytest.fixture
def mock_resource_priority() -> list[str]:
    """Mock resource priority list for agent selectors."""
    return ["cpu", "mem"]


class TestAgentSelectionStrategyFromScalingGroupOpts:
    """Test that agent_selection_strategy is correctly read from ScalingGroupOpts."""

    @pytest.mark.parametrize(
        "strategy",
        [
            AgentSelectionStrategy.DISPERSED,
            AgentSelectionStrategy.CONCENTRATED,
            AgentSelectionStrategy.ROUNDROBIN,
            AgentSelectionStrategy.LEGACY,
        ],
    )
    def test_agent_selection_strategy_from_field(self, strategy: AgentSelectionStrategy) -> None:
        """
        Verify that agent_selection_strategy is correctly read from the field.
        """
        # Given: ScalingGroupOpts with specific agent_selection_strategy
        scheduler_opts = ScalingGroupOpts(agent_selection_strategy=strategy)

        # When: Read from field directly
        actual_strategy = scheduler_opts.agent_selection_strategy

        # Then: Correct value is returned
        assert actual_strategy == strategy

    def test_agent_selection_strategy_default_value(self) -> None:
        """Verify default value is DISPERSED when not specified."""
        # Given: ScalingGroupOpts without explicit agent_selection_strategy
        scheduler_opts = ScalingGroupOpts()

        # When: Read default value
        strategy = scheduler_opts.agent_selection_strategy

        # Then: Default is DISPERSED
        assert strategy == AgentSelectionStrategy.DISPERSED


class TestAgentSelectorPool:
    """Test that agent selector pool contains correct selectors for each strategy."""

    @pytest.mark.parametrize(
        "strategy,expected_selector_type",
        [
            (AgentSelectionStrategy.DISPERSED, DispersedAgentSelector),
            (AgentSelectionStrategy.CONCENTRATED, ConcentratedAgentSelector),
            (AgentSelectionStrategy.ROUNDROBIN, RoundRobinAgentSelector),
            (AgentSelectionStrategy.LEGACY, LegacyAgentSelector),
        ],
    )
    def test_agent_selector_pool_mapping(
        self,
        strategy: AgentSelectionStrategy,
        mock_resource_priority: list[str],
        expected_selector_type: type,
    ) -> None:
        """Verify _make_agent_selector_pool creates correct selector for each strategy."""
        # Given: Create agent selector pool
        pool = SessionProvisioner._make_agent_selector_pool(mock_resource_priority)

        # When: Get selector for strategy
        agent_selector = pool[strategy]

        # Then: Correct selector type is returned
        assert isinstance(agent_selector._strategy, expected_selector_type)


class TestSchedulingDataPath:
    """Test the complete path: SchedulingData -> ScalingGroupMeta -> ScalingGroupOpts -> agent_selection_strategy."""

    @pytest.mark.parametrize(
        "strategy",
        [
            AgentSelectionStrategy.DISPERSED,
            AgentSelectionStrategy.CONCENTRATED,
            AgentSelectionStrategy.ROUNDROBIN,
            AgentSelectionStrategy.LEGACY,
        ],
    )
    def test_agent_selection_strategy_through_scheduling_data(
        self, strategy: AgentSelectionStrategy
    ) -> None:
        """
        Verify the complete path from SchedulingData to agent_selection_strategy.
        """
        # Given: Create complete SchedulingData structure
        scheduler_opts = ScalingGroupOpts(agent_selection_strategy=strategy)

        scaling_group_meta = ScalingGroupMeta(
            name="test-sg",
            scheduler="fifo",
            scheduler_opts=scheduler_opts,
        )

        scheduling_data = SchedulingData(
            scaling_group=scaling_group_meta,
            pending_sessions=PendingSessions(sessions=[]),
            agents=[],
            snapshot_data=None,
            spec=SchedulingSpec(
                known_slot_types={},
                max_container_count=None,
            ),
        )

        # When: Extract agent_selection_strategy from SchedulingData
        # (this mirrors the actual code in provisioner.py:227)
        extracted_strategy = scheduling_data.scaling_group.scheduler_opts.agent_selection_strategy

        # Then: Correct strategy is extracted
        assert extracted_strategy == strategy
