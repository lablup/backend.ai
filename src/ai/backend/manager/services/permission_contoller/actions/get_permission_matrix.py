from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.action.rbac import RBACActionName, RBACRequiredPermission
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class GetPermissionMatrixAction(RoleAction):
    """Action to get the complete RBAC permission matrix.

    Returns scope -> entity -> action_name -> permission mapping.
    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetPermissionMatrixActionResult(BaseActionResult):
    """Result of getting the RBAC permission matrix."""

    matrix: dict[
        RBACElementType, dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]]
    ] = field(default_factory=dict)

    @override
    def entity_id(self) -> str | None:
        return None
