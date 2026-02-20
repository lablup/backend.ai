from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.user.types import BulkUserPurgeResultData, UserInfoContext
from ai.backend.manager.services.user.actions.base import UserAction
from ai.backend.manager.types import OptionalState


@dataclass
class PurgeUserAction(UserAction):
    user_info_ctx: UserInfoContext
    email: str
    purge_shared_vfolders: OptionalState[bool] = field(default_factory=OptionalState.nop)
    delegate_endpoint_ownership: OptionalState[bool] = field(default_factory=OptionalState.nop)

    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class PurgeUserActionResult(BaseActionResult):
    def entity_id(self) -> str | None:
        return None


@dataclass
class BulkPurgeUserAction(UserAction):
    """Action for bulk purging multiple users."""

    user_ids: list[UUID]
    user_info_ctx: UserInfoContext
    purge_shared_vfolders: OptionalState[bool] = field(default_factory=OptionalState.nop)
    delegate_endpoint_ownership: OptionalState[bool] = field(default_factory=OptionalState.nop)

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class BulkPurgeUserActionResult(BaseActionResult):
    """Result of bulk user purge."""

    data: BulkUserPurgeResultData

    @override
    def entity_id(self) -> str | None:
        return None
