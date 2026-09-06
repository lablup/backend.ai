"""Entity type and id of the entity invitations table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ENTITY_SHARE_ENTITY_TYPE", "EntityShareID")

ENTITY_SHARE_ENTITY_TYPE = EntityType("entity_share")


class EntityShareID(EntityIdentifier):
    """An invitation's entity id.

    An invitation is an entity of its own rather than a field of what it offers:
    the invitee acts on it while holding no permission on that entity yet.
    """

    @override
    def entity_type(self) -> EntityType:
        return ENTITY_SHARE_ENTITY_TYPE
