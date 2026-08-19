"""Entity type and id of the vfolder invitations table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("VFOLDER_INVITATION_ENTITY_TYPE", "VFolderInvitationID")

VFOLDER_INVITATION_ENTITY_TYPE = EntityType("vfolder_invitation")


class VFolderInvitationID(EntityIdentifier):
    """An invitation's entity id.

    An invitation is an entity of its own rather than a field of the vfolder:
    the invitee acts on it while holding no permission on the folder yet.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFOLDER_INVITATION_ENTITY_TYPE
