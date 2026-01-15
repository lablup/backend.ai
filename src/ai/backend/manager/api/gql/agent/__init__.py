"""GraphQL types and resolvers for agent and kernel management."""

from __future__ import annotations

from .fetcher import fetch_agents, fetch_kernels_by_agent
from .resolver import agent_stats, agents_v2
from .types import (
    # Agent types
    AgentFilterGQL,
    AgentOrderByGQL,
    AgentResourceGQL,
    AgentStatsGQL,
    AgentV2Connection,
    AgentV2Edge,
    AgentV2GQL,
    # Kernel types
    KernelConnectionV2,
    KernelEdge,
    KernelFilter,
    KernelGQL,
    KernelOrderBy,
    KernelOrderField,
    KernelStatusGQL,
)

__all__ = [
    # Agent types
    "AgentFilterGQL",
    "AgentOrderByGQL",
    "AgentResourceGQL",
    "AgentStatsGQL",
    "AgentV2Connection",
    "AgentV2Edge",
    "AgentV2GQL",
    # Kernel types
    "KernelConnectionV2",
    "KernelEdge",
    "KernelFilter",
    "KernelGQL",
    "KernelOrderBy",
    "KernelOrderField",
    "KernelStatusGQL",
    # Resolvers
    "agent_stats",
    "agents_v2",
    # Fetchers
    "fetch_agents",
    "fetch_kernels_by_agent",
]
