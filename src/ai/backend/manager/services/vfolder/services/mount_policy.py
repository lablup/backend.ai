"""The mount level one user gets on a vfolder, set by whoever may update the folder."""

from __future__ import annotations

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import VFolderMountPolicy
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.errors.storage import (
    VFolderMountPolicyNotApplicable,
    VFolderMountPolicyTooWide,
)
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.vfolder.mount_policy import resolve_mount_policy
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.mount_policy import (
    ListVFolderMountPoliciesAction,
    ListVFolderMountPoliciesActionResult,
    SetVFolderMountPolicyAction,
    SetVFolderMountPolicyActionResult,
    UnsetVFolderMountPolicyAction,
    UnsetVFolderMountPolicyActionResult,
)


class VFolderMountPolicyService:
    _vfolder_repository: VfolderRepository
    _permission_check: RbacPermissionCheckRepository

    def __init__(
        self,
        vfolder_repository: VfolderRepository,
        permission_check: RbacPermissionCheckRepository,
    ) -> None:
        self._vfolder_repository = vfolder_repository
        self._permission_check = permission_check

    def _requester(self) -> UserData:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return me

    async def set(self, action: SetVFolderMountPolicyAction) -> SetVFolderMountPolicyActionResult:
        requester = self._requester()
        vfolder = await self._vfolder_repository.get_by_id(action.vfolder_uuid)
        if vfolder.user is not None and vfolder.user == action.user_id:
            raise VFolderMountPolicyNotApplicable("The owner mounts the folder regardless.")
        if action.user_id == requester.user_id and not requester.is_superadmin:
            raise VFolderMountPolicyNotApplicable("A user cannot set their own mount level.")
        ceiling = await self._ceiling_of(requester, vfolder)
        if ceiling is not None and action.permission.exceeds(ceiling):
            raise VFolderMountPolicyTooWide(
                f"{action.permission.value} exceeds the requester's {ceiling.value} on the folder."
            )
        policy = await self._vfolder_repository.set_user_mount_policy(
            action.vfolder_uuid, action.user_id, action.permission
        )
        return SetVFolderMountPolicyActionResult(policy=policy)

    async def unset(
        self, action: UnsetVFolderMountPolicyAction
    ) -> UnsetVFolderMountPolicyActionResult:
        removed = await self._vfolder_repository.unset_user_mount_policy(
            action.vfolder_uuid, action.user_id
        )
        return UnsetVFolderMountPolicyActionResult(removed=removed)

    async def list(
        self, action: ListVFolderMountPoliciesAction
    ) -> ListVFolderMountPoliciesActionResult:
        policies = await self._vfolder_repository.list_user_mount_policies(action.vfolder_uuid)
        return ListVFolderMountPoliciesActionResult(policies=policies)

    async def _ceiling_of(
        self, requester: UserData, vfolder: VFolderData
    ) -> VFolderMountPolicy | None:
        """The widest level the requester may hand out; ``None`` when unbounded.

        A superadmin, the owner of a personal folder, and whoever holds update on the
        folder through the owning project's roles are unbounded. Anyone else, who
        reaches the folder through a share, may hand out no more than they mount at.
        """
        if requester.is_superadmin:
            return None
        requester_id = UserID(requester.user_id)
        if vfolder.user is not None and vfolder.user == requester_id:
            return None
        if vfolder.group is not None:
            key = GovernCheckKey(
                user_id=requester_id,
                scope=ProjectID(vfolder.group),
                entity_type=VFolderEntityType(),
            )
            governed = await self._permission_check.governed_permissions([key])
            if governed.get(key, Permission.NONE).covers(Permission.UPDATE):
                return None
        held = await self._permission_check.held_permissions(requester_id, [vfolder.id])
        own_rows = await self._vfolder_repository.user_mount_policies_of(
            requester_id, [VFolderUUID(vfolder.id)]
        )
        return resolve_mount_policy(
            requester_id,
            owner_user_id=vfolder.user,
            default_mount_permission=vfolder.default_mount_permission,
            held=held.get(vfolder.id, Permission.NONE),
            user_policy=own_rows.get(VFolderUUID(vfolder.id)),
        )
