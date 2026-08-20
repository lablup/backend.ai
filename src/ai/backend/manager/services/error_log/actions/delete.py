from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.error_log import ErrorLogID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.field.ops import DeleteFieldOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.error_log.updaters import ErrorLogSoftDeleteUpdater
from ai.backend.manager.services.error_log.actions.lookup_owner import LookupErrorLogOwnerAction


@dataclass
class DeleteErrorLogAction(DeleteFieldOpsAction[ErrorLogID, UserID, ErrorLogRow, ErrorLogData]):
    """Clear one error log.

    A log carries no membership of its own, so the user it was recorded against
    answers for the clear.
    """

    log_id: ErrorLogID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_error_log"

    @override
    def field_id(self) -> ErrorLogID:
        return self.log_id

    @override
    def to_owner_lookup_action(self) -> LookupErrorLogOwnerAction:
        return LookupErrorLogOwnerAction(log_id=self.log_id)

    @override
    def to_updater(self) -> ErrorLogSoftDeleteUpdater:
        return ErrorLogSoftDeleteUpdater(log_id=self.log_id)
