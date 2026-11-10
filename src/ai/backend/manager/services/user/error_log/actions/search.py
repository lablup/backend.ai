from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.error_log.scopes import UserErrorLogTarget
from ai.backend.manager.models.error_log.searchers import ErrorLogSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchErrorLogsAction(BulkScopedSearchOpsAction[ErrorLogRow, ErrorLogData]):
    """Page through the errors recorded against the users named, combined with OR.

    Every user is authorized before the read runs.
    """

    user_ids: Sequence[UserID]
    searcher: ErrorLogSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_error_logs"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.user_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [UserErrorLogTarget(user_id=user_id) for user_id in self.user_ids]

    @override
    def to_searcher(self) -> ErrorLogSearcher:
        return self.searcher
