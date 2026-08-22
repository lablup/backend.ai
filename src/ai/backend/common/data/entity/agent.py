from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "AGENT_ENTITY_TYPE",
    "AgentUUID",
)


AGENT_ENTITY_TYPE = EntityType("agent")


class AgentUUID(EntityIdentifier):
    """An agent's entity id.

    Named for the column it comes from: ``agents.id`` is the operator-facing name and
    is already ``AgentId``, so the uuid keeps its own name to stay distinguishable.
    """

    @override
    def entity_type(self) -> EntityType:
        return AGENT_ENTITY_TYPE
