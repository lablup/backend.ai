"""Tests for the shared AgentSelector's internal strategy pool."""

from __future__ import annotations

from ai.backend.common.types import AgentSelectionStrategy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.pool import create_agent_selector


class TestAgentSelectorStrategyPool:
    def test_pool_maps_every_strategy(self) -> None:
        selector = create_agent_selector(["cpu", "mem"])

        assert (
            selector.strategy_name(AgentSelectionStrategy.CONCENTRATED)
            == "ConcentratedAgentSelector"
        )
        assert selector.strategy_name(AgentSelectionStrategy.DISPERSED) == "DispersedAgentSelector"
        assert (
            selector.strategy_name(AgentSelectionStrategy.ROUNDROBIN) == "RoundRobinAgentSelector"
        )
        assert selector.strategy_name(AgentSelectionStrategy.LEGACY) == "LegacyAgentSelector"

    def test_pool_success_messages_are_strategy_specific(self) -> None:
        selector = create_agent_selector(["cpu", "mem"])

        messages = {
            strategy: selector.strategy_success_message(strategy)
            for strategy in AgentSelectionStrategy
        }
        assert len(set(messages.values())) == len(messages)
