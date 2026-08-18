from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.error_log import ERROR_LOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.error_log.searchers import ErrorLogSearcher
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.error_log.types import UserErrorLogOperationScope


@dataclass
class SearchErrorLogsAction(OperationScopeOpsAction[ErrorLogRow, ErrorLogData]):
    """Page through the errors recorded against one user."""

    user_id: UserID
    searcher: ErrorLogSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ERROR_LOG_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (UserErrorLogOperationScope(user_id=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_error_logs"

    @override
    def to_searcher(self) -> ErrorLogSearcher:
        return self.searcher
