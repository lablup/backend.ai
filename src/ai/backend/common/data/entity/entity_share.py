"""Entity type and id of the entity invitations table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("EntityShareEntityType", "EntityShareID")


class EntityShareEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "entity_share"

    @override
    @classmethod
    def description(cls) -> str:
        return "A grant of one entity to another user or project."


class EntityShareID(EntityIdentifier):
    """An invitation's entity id.

    An invitation is an entity of its own rather than a field of what it offers:
    the invitee acts on it while holding no permission on that entity yet.
    """

    @override
    def entity_type(self) -> EntityType:
        return EntityShareEntityType()
