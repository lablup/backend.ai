from __future__ import annotations

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.errors.entity_share import EntityShareNotFound
from ai.backend.manager.models.entity_share.updaters import (
    EntityShareAcceptUpdater,
    EntityShareCancelUpdater,
    EntityShareRejectUpdater,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider

__all__ = ("EntityShareRepository",)


class EntityShareRepository:
    """The three answers an invitation can receive. Creating and reading one is keyed
    on a single spec and goes through ``OpsRepository``.

    Every answer reports the same absence. The guards ride on the statement and do not
    say which of them refused, and telling the invitee whether an id they cannot reach
    exists would answer a question they were not asked.
    """

    _ops: ShareOpsProvider

    def __init__(self, ops_provider: ShareOpsProvider) -> None:
        self._ops = ops_provider

    async def accept(self, share_id: EntityShareID, recipient_user_id: UserID) -> EntityShareData:
        """Take what was offered: the invitation is settled and the entity granted."""
        async with self._ops.write_ops() as w:
            data = await w.accept_invitation(
                EntityShareAcceptUpdater(share_id=share_id, recipient_user_id=recipient_user_id)
            )
            if data is None:
                raise EntityShareNotFound(f"No pending invitation {share_id} to accept")
            return data

    async def reject(self, share_id: EntityShareID, recipient_user_id: UserID) -> EntityShareData:
        """Turn down what was offered, granting nothing."""
        async with self._ops.write_ops() as w:
            data = await w.update_guarded_data(
                EntityShareRejectUpdater(share_id=share_id, recipient_user_id=recipient_user_id)
            )
            if data is None:
                raise EntityShareNotFound(f"No pending invitation {share_id} to reject")
            return data

    async def cancel(self, share_id: EntityShareID) -> EntityShareData:
        """Withdraw the offer before it was answered."""
        async with self._ops.write_ops() as w:
            data = await w.update_guarded_data(EntityShareCancelUpdater(share_id=share_id))
            if data is None:
                raise EntityShareNotFound(f"No pending invitation {share_id} to cancel")
            return data
