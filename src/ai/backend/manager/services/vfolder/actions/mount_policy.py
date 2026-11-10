"""Actions over the mount level one user gets on a vfolder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import VFolderMountPolicy
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderMountPolicyData

from .base import VFolderAction


@dataclass
class SetVFolderMountPolicyAction(VFolderAction):
    """Set the mount level one user gets on the folder, replacing what stood."""

    user_id: UserID
    permission: VFolderMountPolicy

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "set_vfolder_mount_policy"


@dataclass
class SetVFolderMountPolicyActionResult:
    policy: VFolderMountPolicyData


@dataclass
class UnsetVFolderMountPolicyAction(VFolderAction):
    """Take back the mount level one user was given; the folder's default answers again."""

    user_id: UserID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "unset_vfolder_mount_policy"


@dataclass
class UnsetVFolderMountPolicyActionResult:
    removed: bool


@dataclass
class ListVFolderMountPoliciesAction(VFolderAction):
    """The mount levels set on the folder, one row per user."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_vfolder_mount_policies"


@dataclass
class ListVFolderMountPoliciesActionResult:
    policies: list[VFolderMountPolicyData] = field(default_factory=list)
