from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "AgentEntityType",
    "AgentUUID",
)


class AgentEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "agent"

    @override
    @classmethod
    def description(cls) -> str:
        return "A compute node that runs kernels, in one resource group."


class AgentUUID(EntityIdentifier):
    """An agent's entity id.

    Named for the column it comes from: ``agents.id`` is the operator-facing name and
    is already ``AgentId``, so the uuid keeps its own name to stay distinguishable.
    """

    @override
    def entity_type(self) -> EntityType:
        return AgentEntityType()
