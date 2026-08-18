from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.error_log import ERROR_LOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import CreateEntityOpsAction
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.creators import ErrorLogCreator
from ai.backend.manager.models.error_log.row import ErrorLogRow


@dataclass
class CreateErrorLogAction(CreateEntityOpsAction[ErrorLogRow, ErrorLogData]):
    """Record one error against the user it happened to.

    The scope target is the owning user, not the installation: a global gate would
    mean only an administrator may report that something broke for them.
    """

    user_id: UserID
    creator: ErrorLogCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ERROR_LOG_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_error_log"

    @override
    def to_creator(self) -> ErrorLogCreator:
        return self.creator
