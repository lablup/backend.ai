import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import (
    EntityType,
    RBACElementType,
    ScopeType,
)
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder import VFolderPermission
from ai.backend.manager.services.vfolder.actions.base import VFolderScopeActionResult


@dataclass
class CreateVFolderV2Action(BaseScopeAction):
    """Create a new vfolder. Policy is resolved internally from user_id."""

    name: str
    user_id: uuid.UUID
    domain_name: str
    project_id: uuid.UUID | None
    host: str | None
    usage_mode: VFolderUsageMode
    permission: VFolderPermission
    cloneable: bool
    owner_id: UserID | None = None
    """Delegated owner user UUID. When set, the service resolves it and creates
    the vfolder owned by that user instead of the caller."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.VFOLDER

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT if self.project_id else ScopeType.USER

    @override
    def scope_id(self) -> str:
        if self.project_id:
            return str(self.project_id)
        # When delegating, authorize against the owner's USER scope.
        return str(self.owner_id) if self.owner_id is not None else str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        if self.project_id:
            return RBACElementRef(
                element_type=RBACElementType.PROJECT,
                element_id=str(self.project_id),
            )
        # When delegating (owner_id set), authorize the caller against the
        # owner's USER scope, not the caller's own.
        target_user_id = self.owner_id if self.owner_id is not None else self.user_id
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(target_user_id),
        )


@dataclass
class CreateVFolderV2ActionResult(VFolderScopeActionResult):
    vfolder: VFolderData

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder.id)

    @override
    def scope_type(self) -> ScopeType:
        # The created vfolder is either project-owned or user-owned.
        return ScopeType.PROJECT if self.vfolder.group is not None else ScopeType.USER

    @override
    def scope_id(self) -> str:
        scope_owner = self.vfolder.group if self.vfolder.group is not None else self.vfolder.user
        return str(scope_owner)
