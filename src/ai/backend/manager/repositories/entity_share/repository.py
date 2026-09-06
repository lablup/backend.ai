from __future__ import annotations

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.errors.entity_share import EntityShareNotFound
from ai.backend.manager.models.entity_share.creators import EntityShareCreator
from ai.backend.manager.models.entity_share.updaters import (
    EntityShareAcceptUpdater,
    EntityShareCancelUpdater,
    EntityShareLeaveUpdater,
    EntityShareRejectUpdater,
    EntityShareRevokeUpdater,
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

    async def create(self, creator: EntityShareCreator) -> EntityShareData:
        """Write the offer, or restate what already stands for the same pair.

        One live row stands per recipient and entity, so offering again to somewhere
        that already holds the entity sets what it lends rather than adding a second
        row. Looking and writing share one transaction, so two offers racing cannot
        both decide nothing stands.
        """
        async with self._ops.write_ops() as w:
            restated = await w.restate_share(creator)
            if restated is not None:
                return restated
            return await w.create_entity(creator)

    async def accept(
        self, share_id: EntityShareID, answering_scope: EntityIdentifier
    ) -> EntityShareData:
        """Take what was offered: the offer is settled and the entity lent."""
        async with self._ops.write_ops() as w:
            data = await w.accept_share(
                EntityShareAcceptUpdater(share_id=share_id, answering_scope=answering_scope)
            )
            if data is None:
                raise EntityShareNotFound(f"No open offer {share_id} to accept")
            return data

    async def reject(
        self, share_id: EntityShareID, answering_scope: EntityIdentifier
    ) -> EntityShareData:
        """Turn down what was offered, lending nothing."""
        async with self._ops.write_ops() as w:
            data = await w.update_guarded_data(
                EntityShareRejectUpdater(share_id=share_id, answering_scope=answering_scope)
            )
            if data is None:
                raise EntityShareNotFound(f"No open offer {share_id} to reject")
            return data

    async def revoke(self, share_id: EntityShareID) -> EntityShareData:
        """Take back what was lent, from wherever it landed."""
        async with self._ops.write_ops() as w:
            data = await w.revoke_share(EntityShareRevokeUpdater(share_id=share_id))
            if data is None:
                raise EntityShareNotFound(f"No held share {share_id} to take back")
            return data

    async def leave(
        self, share_id: EntityShareID, answering_scope: EntityIdentifier
    ) -> EntityShareData:
        """Give back what was taken."""
        async with self._ops.write_ops() as w:
            data = await w.revoke_share(
                EntityShareLeaveUpdater(share_id=share_id, answering_scope=answering_scope)
            )
            if data is None:
                raise EntityShareNotFound(f"No held share {share_id} to give back")
            return data

    async def cancel(self, share_id: EntityShareID) -> EntityShareData:
        """Withdraw the offer before it was answered."""
        async with self._ops.write_ops() as w:
            data = await w.update_guarded_data(EntityShareCancelUpdater(share_id=share_id))
            if data is None:
                raise EntityShareNotFound(f"No open offer {share_id} to cancel")
            return data
