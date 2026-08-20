from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import CreateFieldOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.creators import ErrorLogCreator
from ai.backend.manager.models.error_log.row import ErrorLogRow


@dataclass
class CreateErrorLogAction(CreateFieldOpsAction[UserID, ErrorLogRow, ErrorLogData]):
    """Record one error against the user it happened to.

    The target is that user: writing a log under them is answered for like an update
    to the user, so anyone may report what broke for them.
    """

    user_id: UserID
    creator: ErrorLogCreator

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def owner_id(self) -> UserID:
        return self.user_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_error_log"

    @override
    def to_creator(self) -> ErrorLogCreator:
        return self.creator
