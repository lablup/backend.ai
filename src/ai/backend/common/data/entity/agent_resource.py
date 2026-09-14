from typing import override

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("AgentResourceID",)


class AgentResourceFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "agent_resource"

    @override
    @classmethod
    def description(cls) -> str:
        return "One slot's capacity and usage on one agent."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return AgentEntityType


class AgentResourceID(FieldIdentifier):
    """One slot's amount on one agent."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return AgentResourceFieldType()
