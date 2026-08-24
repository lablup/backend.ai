"""Entity type and id of the entity invitations table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ENTITY_INVITATION_ENTITY_TYPE", "EntityInvitationID")

ENTITY_INVITATION_ENTITY_TYPE = EntityType("entity_invitation")


class EntityInvitationID(EntityIdentifier):
    """An invitation's entity id.

    An invitation is an entity of its own rather than a field of what it offers:
    the invitee acts on it while holding no permission on that entity yet.
    """

    @override
    def entity_type(self) -> EntityType:
        return ENTITY_INVITATION_ENTITY_TYPE
