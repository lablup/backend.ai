from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.user.queriers import BulkUserQuerier
from ai.backend.manager.models.user.row import UserRow


@dataclass
class BulkGetUsersAction(PartialBulkGetEntityOpsAction[UserRow, UserData]):
    """Read the users the caller named, answering for each id."""

    ids: Sequence[UserID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_users"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkUserQuerier:
        return BulkUserQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
