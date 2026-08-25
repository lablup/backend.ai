from __future__ import annotations

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.errors.entity_invitation import EntityInvitationNotFound
from ai.backend.manager.models.entity_invitation.updaters import (
    EntityInvitationAcceptUpdater,
    EntityInvitationCancelUpdater,
    EntityInvitationRejectUpdater,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("EntityInvitationRepository",)


class EntityInvitationRepository:
    """The three answers an invitation can receive. Creating and reading one is keyed
    on a single spec and goes through ``OpsRepository``.

    Every answer reports the same absence. The guards ride on the statement and do not
    say which of them refused, and telling the invitee whether an id they cannot reach
    exists would answer a question they were not asked.
    """

    _ops: V2DBOpsProvider

    def __init__(self, v2_ops_provider: V2DBOpsProvider) -> None:
        self._ops = v2_ops_provider

    async def accept(
        self, invitation_id: EntityInvitationID, invitee_user_id: UserID
    ) -> EntityInvitationData:
        """Take what was offered: the invitation is settled and the entity granted."""
        async with self._ops.write_ops() as w:
            data = await w.accept_entity_invitation(
                EntityInvitationAcceptUpdater(
                    invitation_id=invitation_id, invitee_user_id=invitee_user_id
                )
            )
            if data is None:
                raise EntityInvitationNotFound(f"No pending invitation {invitation_id} to accept")
            return data

    async def reject(
        self, invitation_id: EntityInvitationID, invitee_user_id: UserID
    ) -> EntityInvitationData:
        """Turn down what was offered, granting nothing."""
        async with self._ops.write_ops() as w:
            data = await w.update_guarded_data(
                EntityInvitationRejectUpdater(
                    invitation_id=invitation_id, invitee_user_id=invitee_user_id
                )
            )
            if data is None:
                raise EntityInvitationNotFound(f"No pending invitation {invitation_id} to reject")
            return data

    async def cancel(self, invitation_id: EntityInvitationID) -> EntityInvitationData:
        """Withdraw the offer before it was answered."""
        async with self._ops.write_ops() as w:
            data = await w.update_guarded_data(
                EntityInvitationCancelUpdater(invitation_id=invitation_id)
            )
            if data is None:
                raise EntityInvitationNotFound(f"No pending invitation {invitation_id} to cancel")
            return data
