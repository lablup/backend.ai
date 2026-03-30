"""RBAC action declarations for the VFOLDER element type."""

from typing import override

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)


class VFolderCreateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.CREATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.CREATE)


class VFolderGetRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GET

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.READ)


class VFolderSearchRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SEARCH

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.READ)


class VFolderUpdateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.UPDATE)


class VFolderSoftDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SOFT_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.SOFT_DELETE)


class VFolderHardDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.HARD_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.HARD_DELETE)


class VFolderGrantAllRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_ALL

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_ALL)


class VFolderGrantReadRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_READ

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_READ)


class VFolderGrantUpdateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_UPDATE)


class VFolderGrantSoftDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_SOFT_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_SOFT_DELETE)


class VFolderGrantHardDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_HARD_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_HARD_DELETE)
