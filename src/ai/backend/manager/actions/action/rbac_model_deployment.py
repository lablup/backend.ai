"""RBAC action declarations for the MODEL_DEPLOYMENT element type."""

from typing import override

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)


class ModelDeploymentCreateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.CREATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.MODEL_DEPLOYMENT, OperationType.CREATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT


class ModelDeploymentGetRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GET

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.MODEL_DEPLOYMENT, OperationType.READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT


class ModelDeploymentSearchRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SEARCH

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.MODEL_DEPLOYMENT, OperationType.READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT


class ModelDeploymentUpdateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.MODEL_DEPLOYMENT, OperationType.UPDATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT


class ModelDeploymentHardDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.HARD_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.MODEL_DEPLOYMENT, OperationType.HARD_DELETE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT
