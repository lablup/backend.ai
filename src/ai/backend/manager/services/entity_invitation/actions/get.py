"""Read one invitation from the side that offered it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.models.entity_invitation.queriers import EntityInvitationQuerier
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow

__all__ = ("GetEntityInvitationAction",)


@dataclass
class GetEntityInvitationAction(
    GetSingleEntityOpsAction[EntityInvitationRow, EntityInvitationData]
):
    """Read one invitation by id.

    Answered for by the invitation, which belongs to the entity it offers — so this is
    the offering side's read. The invitee reaches theirs through the search addressed
    to them, having no permission on the invitation itself.
    """

    invitation_id: EntityInvitationID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_entity_invitation"

    @override
    def entity_id(self) -> EntityInvitationID:
        return self.invitation_id

    @override
    def to_querier(self) -> EntityInvitationQuerier:
        return EntityInvitationQuerier(invitation_id=self.invitation_id)
