"""RBAC action declarations for the SESSION element type."""

from typing import override

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)


class SessionCreateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.CREATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.CREATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class SessionGetRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GET

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class SessionSearchRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SEARCH

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class SessionUpdateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.UPDATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class SessionHardDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.HARD_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.HARD_DELETE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class SessionGrantAllRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_ALL

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.GRANT_ALL)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class SessionGrantReadRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_READ

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.GRANT_READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class SessionGrantUpdateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.GRANT_UPDATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class SessionGrantHardDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_HARD_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.SESSION, OperationType.GRANT_HARD_DELETE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER
