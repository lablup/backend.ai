from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.user.types import BulkUserPurgeResultData
from ai.backend.manager.types import OptionalState

__all__ = (
    "PurgeUserAction",
    "PurgeUserActionResult",
    "BulkPurgeUserAction",
    "BulkPurgeUserActionResult",
)


@dataclass(frozen=True)
class PurgeUserAction(BaseSingleEntityAction):
    """Remove one user for good, with everything they owned."""

    user_id: UserID
    admin_user_id: UUID
    purge_shared_vfolders: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    delegate_endpoint_ownership: OptionalState[bool] = field(
        default_factory=OptionalState[bool].nop
    )

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_user"


@dataclass(frozen=True)
class PurgeUserActionResult:
    user_uuid: UUID


@dataclass(frozen=True)
class BulkPurgeUserAction(BaseGlobalAction):
    """Remove several users at once, across domains."""

    user_ids: list[UUID]
    admin_user_id: UUID
    purge_shared_vfolders: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    delegate_endpoint_ownership: OptionalState[bool] = field(
        default_factory=OptionalState[bool].nop
    )

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_purge_users"


@dataclass(frozen=True)
class BulkPurgeUserActionResult:
    data: BulkUserPurgeResultData
