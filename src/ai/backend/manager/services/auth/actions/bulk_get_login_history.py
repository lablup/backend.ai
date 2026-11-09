from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.login_history import LoginHistoryID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.auth.login_session_types import LoginHistoryData
from ai.backend.manager.models.login_session.queriers import BulkLoginHistoryQuerier
from ai.backend.manager.models.login_session.row import LoginHistoryRow
from ai.backend.manager.services.auth.actions.lookup_login_history_owner import (
    LookupBulkLoginHistoryOwnerAction,
)


@dataclass
class BulkGetLoginHistoryAction(
    PartialBulkGetFieldOpsAction[LoginHistoryID, UserID, LoginHistoryRow, LoginHistoryData]
):
    """Read the login history rows the caller named."""

    ids: Sequence[LoginHistoryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_login_history"

    @override
    def field_ids(self) -> Sequence[LoginHistoryID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkLoginHistoryOwnerAction:
        return LookupBulkLoginHistoryOwnerAction(attempt_ids=self.ids)

    @override
    def to_querier(self) -> BulkLoginHistoryQuerier:
        return BulkLoginHistoryQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[LoginHistoryID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
