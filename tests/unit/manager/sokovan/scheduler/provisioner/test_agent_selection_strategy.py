"""Tests for the agent selector pool keyed by AgentSelectionStrategy."""

from __future__ import annotations

from ai.backend.common.types import AgentSelectionStrategy
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import SessionProvisioner


class TestAgentSelectorPool:
    def test_pool_maps_every_strategy(self) -> None:
        pool = SessionProvisioner._make_agent_selector_pool(["cpu", "mem"])

        assert (
            pool[AgentSelectionStrategy.CONCENTRATED].strategy_name() == "ConcentratedAgentSelector"
        )
        assert pool[AgentSelectionStrategy.DISPERSED].strategy_name() == "DispersedAgentSelector"
        assert pool[AgentSelectionStrategy.ROUNDROBIN].strategy_name() == "RoundRobinAgentSelector"
        assert pool[AgentSelectionStrategy.LEGACY].strategy_name() == "LegacyAgentSelector"

    def test_pool_success_messages_are_strategy_specific(self) -> None:
        pool = SessionProvisioner._make_agent_selector_pool(["cpu", "mem"])

        messages = {
            strategy: pool[strategy].strategy_success_message()
            for strategy in AgentSelectionStrategy
        }
        assert len(set(messages.values())) == len(messages)
