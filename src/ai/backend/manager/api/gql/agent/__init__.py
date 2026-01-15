"""GraphQL types and resolvers for agent management."""

from __future__ import annotations

from .fetcher import fetch_agents
from .resolver import agent_stats, agents_v2
from .types import (
    AgentFilterGQL,
    AgentOrderByGQL,
    AgentResourceGQL,
    AgentStatsGQL,
    AgentV2Connection,
    AgentV2Edge,
    AgentV2GQL,
)

__all__ = (
    # Types
    "AgentFilterGQL",
    "AgentOrderByGQL",
    "AgentResourceGQL",
    "AgentStatsGQL",
    "AgentV2GQL",
    "AgentV2Connection",
    "AgentV2Edge",
    # Resolvers
    "agent_stats",
    "agents_v2",
    # Fetchers
    "fetch_agents",
)
