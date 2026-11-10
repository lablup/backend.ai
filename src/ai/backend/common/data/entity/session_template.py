"""Entity type and id of the session templates table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("SessionTemplateEntityType", "SessionTemplateID")


class SessionTemplateEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "session_template"

    @override
    @classmethod
    def description(cls) -> str:
        return "A saved setting a session can be created from."


class SessionTemplateID(EntityIdentifier):
    """A session template's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return SessionTemplateEntityType()
