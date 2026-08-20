from typing import override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier, FieldType

__all__ = ("AgentResourceID",)


AGENT_RESOURCE_FIELD_TYPE = FieldType("agent_resource")


class AgentResourceID(FieldIdentifier):
    """One slot's amount on one agent."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return AGENT_RESOURCE_FIELD_TYPE

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return AGENT_ENTITY_TYPE
