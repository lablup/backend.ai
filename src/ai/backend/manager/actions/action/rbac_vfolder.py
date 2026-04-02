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

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderGetRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GET

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderSearchRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SEARCH

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderUpdateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.UPDATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderSoftDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SOFT_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.SOFT_DELETE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderHardDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.HARD_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.HARD_DELETE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderGrantAllRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_ALL

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_ALL)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderGrantReadRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_READ

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderGrantUpdateRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_UPDATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderGrantSoftDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_SOFT_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_SOFT_DELETE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


class VFolderGrantHardDeleteRBACAction(BaseRBACAction):
    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.GRANT_HARD_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.VFOLDER, OperationType.GRANT_HARD_DELETE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER
