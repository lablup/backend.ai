from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.login_session import LoginSessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.auth.login_session_types import LoginSessionData
from ai.backend.manager.models.login_session.queriers import BulkLoginSessionQuerier
from ai.backend.manager.models.login_session.row import LoginSessionRow
from ai.backend.manager.services.auth.actions.lookup_login_session_owner import (
    LookupBulkLoginSessionOwnerAction,
)


@dataclass
class BulkGetLoginSessionsAction(
    PartialBulkGetFieldOpsAction[LoginSessionID, UserID, LoginSessionRow, LoginSessionData]
):
    """Read the login sessions the caller named."""

    ids: Sequence[LoginSessionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_login_sessions"

    @override
    def field_ids(self) -> Sequence[LoginSessionID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkLoginSessionOwnerAction:
        return LookupBulkLoginSessionOwnerAction(session_ids=self.ids)

    @override
    def to_querier(self) -> BulkLoginSessionQuerier:
        return BulkLoginSessionQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[LoginSessionID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
