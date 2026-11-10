from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.row import ErrorLogRow


@dataclass(frozen=True)
class GlobalSearchErrorLogsAction(GlobalSearcherOpsAction[ErrorLogRow, ErrorLogData]):
    """Page through every recorded error — the super-admin read."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_error_logs"
