from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.error_log import ERROR_LOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.creators import ErrorLogCreator
from ai.backend.manager.models.error_logs import ErrorLogRow


@dataclass
class CreateErrorLogAction(CreateGlobalOpsAction[ErrorLogRow, ErrorLogData]):
    """Record one error."""

    creator: ErrorLogCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ERROR_LOG_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_error_log"

    @override
    def to_creator(self) -> ErrorLogCreator:
        return self.creator
