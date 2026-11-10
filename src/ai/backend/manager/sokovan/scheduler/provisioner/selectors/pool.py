"""Default construction of the shared :class:`AgentSelector`.

Kept out of ``selector.py`` so the selector module does not import the
concrete strategies (they subclass its ``AbstractAgentSelector``).
"""

from __future__ import annotations

from collections import defaultdict

from ai.backend.common.types import AgentSelectionStrategy

from .concentrated import ConcentratedAgentSelector
from .dispersed import DispersedAgentSelector
from .filters.exclusion.architecture import ArchitectureTrackerFilter
from .filters.exclusion.designated_strict import DesignatedStrictTrackerFilter
from .filters.exclusion.session_group_strict import SessionGroupStrictTrackerFilter
from .filters.stateful.container_limit import ContainerLimitTrackerFilter
from .filters.stateful.resource import ResourceTrackerFilter
from .legacy import LegacyAgentSelector
from .orders.designated_preferred import DesignatedPreferredOrder
from .orders.failed_session import FailedSessionOrder
from .orders.session_group import SessionGroupOrder
from .roundrobin import RoundRobinAgentSelector
from .selector import AbstractAgentSelector, AgentSelector
from .victims.pool import create_victim_selector


def create_agent_selector(agent_selection_resource_priority: list[str]) -> AgentSelector:
    """Build the one selector instance shared across scheduling, holding the
    full strategy pool (unknown strategies fall back to concentrated)."""
    strategy_pool: dict[AgentSelectionStrategy, AbstractAgentSelector] = defaultdict(
        lambda: ConcentratedAgentSelector(agent_selection_resource_priority)
    )
    strategy_pool[AgentSelectionStrategy.CONCENTRATED] = ConcentratedAgentSelector(
        agent_selection_resource_priority
    )
    strategy_pool[AgentSelectionStrategy.DISPERSED] = DispersedAgentSelector(
        agent_selection_resource_priority
    )
    strategy_pool[AgentSelectionStrategy.ROUNDROBIN] = RoundRobinAgentSelector()
    strategy_pool[AgentSelectionStrategy.LEGACY] = LegacyAgentSelector(
        agent_selection_resource_priority
    )
    # Filter and order sequence carry the placement precedence: the more
    # local target applies first (designated agents > session group > the
    # resource group's strategy, which picks from what is left).
    return AgentSelector(
        strategy_pool,
        exclusion_filters=[
            ArchitectureTrackerFilter(),
            DesignatedStrictTrackerFilter(),
            SessionGroupStrictTrackerFilter(),
        ],
        stateful_filters=[ResourceTrackerFilter(), ContainerLimitTrackerFilter()],
        orders=[DesignatedPreferredOrder(), SessionGroupOrder(), FailedSessionOrder()],
        victim_selector=create_victim_selector(),
    )
