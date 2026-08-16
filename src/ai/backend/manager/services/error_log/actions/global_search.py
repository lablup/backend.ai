from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.error_log import ERROR_LOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.repositories.error_log.searchers import ErrorLogSearcher


@dataclass
class GlobalSearchErrorLogsAction(SearchGlobalOpsAction[ErrorLogRow, ErrorLogData]):
    """Page through every recorded error — the super-admin read."""

    searcher: ErrorLogSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ERROR_LOG_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_error_logs"

    @override
    def to_searcher(self) -> ErrorLogSearcher:
        return self.searcher
