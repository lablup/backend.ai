from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.error_log import ErrorLogID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.updaters import ErrorLogSoftDeleteUpdater
from ai.backend.manager.models.error_logs import ErrorLogRow


@dataclass
class DeleteErrorLogAction(DeleteSingleEntityOpsAction[ErrorLogRow, ErrorLogData]):
    """Clear one error log.

    The target is the log itself, so the question is whether the caller may delete
    that row. Who the caller is comes from the request context.
    """

    log_id: ErrorLogID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.log_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_error_log"

    @override
    def to_updater(self) -> ErrorLogSoftDeleteUpdater:
        return ErrorLogSoftDeleteUpdater(log_id=self.log_id)
