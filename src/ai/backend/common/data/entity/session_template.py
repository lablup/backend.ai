"""Entity type and id of the session templates table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("SESSION_TEMPLATE_ENTITY_TYPE", "SessionTemplateID")

SESSION_TEMPLATE_ENTITY_TYPE = EntityType("session_template")


class SessionTemplateID(EntityIdentifier):
    """A session template's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return SESSION_TEMPLATE_ENTITY_TYPE
