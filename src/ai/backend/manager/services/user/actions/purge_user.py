from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import BulkUserPurgeResultData, UserInfoContext
from ai.backend.manager.services.user.actions.base import (
    UserAction,
    UserSingleEntityAction,
    UserSingleEntityActionResult,
)
from ai.backend.manager.types import OptionalState


@dataclass
class PurgeUserAction(UserSingleEntityAction):
    user_info_ctx: UserInfoContext
    email: str  # Still needed for the service layer implementation
    purge_shared_vfolders: OptionalState[bool] = field(default_factory=OptionalState.nop)
    delegate_endpoint_ownership: OptionalState[bool] = field(default_factory=OptionalState.nop)
    user_uuid: UUID | None = None  # Set by API layer for RBAC validation

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def target_entity_id(self) -> str:
        if self.user_uuid is None:
            raise ValueError("user_uuid must be set for RBAC validation")
        return str(self.user_uuid)

    @override
    def target_element(self) -> RBACElementRef:
        if self.user_uuid is None:
            raise ValueError("user_uuid must be set for RBAC validation")
        return RBACElementRef(RBACElementType.USER, str(self.user_uuid))


@dataclass
class PurgeUserActionResult(UserSingleEntityActionResult):
    user_uuid: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.user_uuid)


@dataclass
class BulkPurgeUserAction(UserAction):
    """Action for bulk purging multiple users."""

    user_ids: list[UUID]
    admin_user_id: UUID
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
