"""RBAC action declarations for the USER element type."""

from typing import override

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)


class UserCreateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.CREATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.USER, OperationType.CREATE)


class UserGetRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GET

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.USER, OperationType.READ)


class UserSearchRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SEARCH

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.USER, OperationType.READ)


class UserUpdateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.USER, OperationType.UPDATE)


class UserSoftDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SOFT_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.USER, OperationType.SOFT_DELETE)


class UserHardDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.HARD_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.USER, OperationType.HARD_DELETE)
