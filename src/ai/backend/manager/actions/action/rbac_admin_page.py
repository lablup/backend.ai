"""RBAC action declarations for admin-page access control element types.

These are pseudo-entities that gate visibility of the project admin page.
They carry only a READ operation and are not enforced at runtime like CRUD
actions; they exist so that the permission matrix exposes an assignable
operation for custom roles.
"""

from typing import override

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)


class ProjectAdminPageGetRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GET

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.PROJECT_ADMIN_PAGE, OperationType.READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT
