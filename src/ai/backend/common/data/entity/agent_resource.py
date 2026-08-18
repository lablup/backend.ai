from typing import override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("AgentResourceID",)


class AgentResourceID(FieldIdentifier):
    """One slot's amount on one agent."""

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return AGENT_ENTITY_TYPE
