"""Entity type and id of the vfolder invitations table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("VFolderInvitationEntityType", "VFolderInvitationID")


class VFolderInvitationEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "vfolder_invitation"

    @override
    @classmethod
    def description(cls) -> str:
        return "An invitation to share a vfolder with a user."


class VFolderInvitationID(EntityIdentifier):
    """An invitation's entity id.

    An invitation is an entity of its own rather than a field of the vfolder:
    the invitee acts on it while holding no permission on the folder yet.
    """

    @override
    def entity_type(self) -> EntityType:
        return VFolderInvitationEntityType()
