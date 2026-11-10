from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.queriers import (
    BulkSessionSchedulingHistoryQuerier,
)
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.services.scheduling_history.actions.lookup_owner import (
    LookupBulkSessionSchedulingHistoryOwnerAction,
)


@dataclass
class BulkGetSessionHistoriesAction(
    PartialBulkGetFieldOpsAction[
        SessionSchedulingHistoryID,
        SessionID,
        SessionSchedulingHistoryRow,
        SessionSchedulingHistoryData,
    ]
):
    """Read the session scheduling history rows the caller named."""

    ids: Sequence[SessionSchedulingHistoryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_session_histories"

    @override
    def field_ids(self) -> Sequence[SessionSchedulingHistoryID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkSessionSchedulingHistoryOwnerAction:
        return LookupBulkSessionSchedulingHistoryOwnerAction(history_ids=self.ids)

    @override
    def to_querier(self) -> BulkSessionSchedulingHistoryQuerier:
        return BulkSessionSchedulingHistoryQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[SessionSchedulingHistoryID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
