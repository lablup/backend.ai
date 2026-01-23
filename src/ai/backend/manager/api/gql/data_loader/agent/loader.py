from collections.abc import Sequence

from ai.backend.common.resource.types import AgentResourceData
from ai.backend.common.types import AgentId
from ai.backend.manager.services.agent.actions.load_agent_resources import (
    LoadAgentResourcesAction,
)
from ai.backend.manager.services.agent.actions.load_container_counts import (
    LoadContainerCountsAction,
)
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


async def load_agent_resources(
    processor: AgentProcessors,
    agent_ids: Sequence[AgentId],
) -> list[AgentResourceData]:
    """Batch load agent resources for agents by their IDs.

    Args:
        processor: AgentProcessors instance.
        agent_ids: List of agent IDs to load resources for.

    Returns:
        List of AgentResourceData in the same order as agent_ids.
    """
    if not agent_ids:
        return []

    action_result = await processor.load_agent_resources.wait_for_complete(
        LoadAgentResourcesAction(agent_ids=agent_ids)
    )

    # Return AgentResourceData in the same order as input agent_ids
    result: list[AgentResourceData] = []
    for agent_id in agent_ids:
        resource_data = action_result.agent_resources.get(agent_id, AgentResourceData.empty())
        result.append(resource_data)
    return result
