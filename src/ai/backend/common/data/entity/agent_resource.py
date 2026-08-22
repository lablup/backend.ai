from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("AgentResourceID",)


AGENT_RESOURCE_FIELD_TYPE = FieldType("agent_resource")


class AgentResourceID(FieldIdentifier):
    """One slot's amount on one agent."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return AGENT_RESOURCE_FIELD_TYPE
