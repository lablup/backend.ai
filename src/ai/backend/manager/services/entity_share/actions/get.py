"""Read one invitation from the side that offered it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.queriers import EntityShareQuerier
from ai.backend.manager.models.entity_share.row import EntityShareRow

__all__ = ("GetEntityShareAction",)


@dataclass
class GetEntityShareAction(GetSingleEntityOpsAction[EntityShareRow, EntityShareData]):
    """Read one invitation by id.

    Answered for by the invitation, which belongs to the entity it offers — so this is
    the offering side's read. The invitee reaches theirs through the search addressed
    to them, having no permission on the invitation itself.
    """

    share_id: EntityShareID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_entity_share"

    @override
    def entity_id(self) -> EntityShareID:
        return self.share_id

    @override
    def to_querier(self) -> EntityShareQuerier:
        return EntityShareQuerier(share_id=self.share_id)
