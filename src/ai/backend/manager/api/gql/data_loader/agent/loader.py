from collections.abc import Sequence

from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentDetailData
from ai.backend.manager.repositories.agent.options import AgentConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.services.agent.actions.load_container_counts import (
    LoadContainerCountsAction,
)
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction
from ai.backend.manager.services.agent.processors import AgentProcessors


async def load_container_counts(
    processor: AgentProcessors,
    agent_ids: Sequence[AgentId],
) -> list[int]:
    """Batch load container counts for agents by their IDs.

    Args:
        processor: AgentProcessors instance.
        agent_ids: List of agent IDs to load container counts for.

    Returns:
        List of container counts in the same order as agent_ids.
    """
    if not agent_ids:
        return []

    action_result = await processor.load_container_counts.wait_for_complete(
        LoadContainerCountsAction(agent_ids=agent_ids)
    )

    # container_counts is already in the same order as input agent_ids
    return list(action_result.container_counts)


async def load_agents_by_ids(
    processor: AgentProcessors,
    agent_ids: Sequence[AgentId],
) -> list[AgentDetailData | None]:
    """Batch load agents by their IDs.

    Args:
        processor: AgentProcessors instance.
        agent_ids: Sequence of agent IDs to load.

    Returns:
        List of AgentDetailData (or None if not found) in the same order as agent_ids.
    """
    if not agent_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[AgentConditions.by_ids(agent_ids)],
    )

    action_result = await processor.search_agents.wait_for_complete(
        SearchAgentsAction(querier=querier)
    )

    agent_map = {agent_detail.agent.id: agent_detail for agent_detail in action_result.agents}
    return [agent_map.get(agent_id) for agent_id in agent_ids]
