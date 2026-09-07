from typing import Any

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserData
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.vfolder import VFolderOwnershipType
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.sharing import (
    GlobalListSharedVFoldersAction,
    GlobalListSharedVFoldersActionResult,
    ListSharedVFoldersAction,
    ListSharedVFoldersActionResult,
    PublicListSharedVFoldersAction,
    PublicListSharedVFoldersActionResult,
    ShareVFolderAction,
    ShareVFolderActionResult,
    UnshareVFolderAction,
    UnshareVFolderActionResult,
    UpdateVFolderSharingStatusAction,
    UpdateVFolderSharingStatusActionResult,
    VFolderSharedInfo,
)


class VFolderSharingService:
    _config_provider: ManagerConfigProvider
    _vfolder_repository: VfolderRepository
    _user_repository: UserRepository

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        vfolder_repository: VfolderRepository,
        user_repository: UserRepository,
    ) -> None:
        self._config_provider = config_provider
        self._vfolder_repository = vfolder_repository
        self._user_repository = user_repository

    def _requester(self) -> UserData:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        return me

    async def share(self, action: ShareVFolderAction) -> ShareVFolderActionResult:
        requester_id = self._requester().user_id
        user = await self._user_repository.get_user_by_uuid(requester_id)
        if not user.domain_name:
            raise VFolderNotFound("User has no domain assigned")
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        if vfolder_data.ownership_type != VFolderOwnershipType.GROUP:
            raise VFolderNotFound("Only project folders are directly sharable.")

        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        shared_emails = await self._vfolder_repository.share_vfolder_with_users(
            vfolder_id=action.vfolder_uuid,
            vfolder_host=vfolder_data.host,
            vfolder_group=vfolder_data.group,
            requester_uuid=requester_id,
            requester_email=user.email,
            domain_name=user.domain_name,
            resource_policy=action.resource_policy,
            emails=action.emails,
            permission=action.permission,
            allowed_vfolder_types=list(allowed_vfolder_types),
        )
        return ShareVFolderActionResult(shared_emails=shared_emails)

    async def unshare(self, action: UnshareVFolderAction) -> UnshareVFolderActionResult:
        requester_id = self._requester().user_id
        user = await self._user_repository.get_user_by_uuid(requester_id)
        if not user.domain_name:
            raise VFolderNotFound("User has no domain assigned")
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        if vfolder_data.ownership_type != VFolderOwnershipType.GROUP:
            raise VFolderNotFound("Only project folders are directly unsharable.")

        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        unshared_emails = await self._vfolder_repository.unshare_vfolder_from_users(
            vfolder_id=action.vfolder_uuid,
            vfolder_host=vfolder_data.host,
            requester_uuid=requester_id,
            domain_name=user.domain_name,
            resource_policy=action.resource_policy,
            emails=action.emails,
            allowed_vfolder_types=list(allowed_vfolder_types),
        )
        return UnshareVFolderActionResult(unshared_emails=unshared_emails)

    def _to_shared_info(self, rows: list[dict[str, Any]]) -> list[VFolderSharedInfo]:
        shared_info = []
        for row in rows:
            is_project_folder = row["ownership_type"] == VFolderOwnershipType.GROUP
            owner = row["group"] if is_project_folder else row["vfolder_user"]
            folder_type = "project" if is_project_folder else "user"
            shared_info.append(
                VFolderSharedInfo(
                    vfolder_id=row["vfolder_id"],
                    vfolder_name=row["name"],
                    status=row["status"],
                    owner=str(owner),
                    folder_type=folder_type,
                    shared_user_uuid=row["user"],
                    shared_user_email=row["email"],
                    permission=row["permission"],
                )
            )
        return shared_info

    async def list_shared_vfolders(
        self, action: ListSharedVFoldersAction
    ) -> ListSharedVFoldersActionResult:
        raw_list = await self._vfolder_repository.list_shared_vfolder_permissions(
            vfolder_id=action.vfolder_uuid
        )
        return ListSharedVFoldersActionResult(shared=self._to_shared_info(raw_list))

    async def public_list_shared_vfolders(
        self, action: PublicListSharedVFoldersAction
    ) -> PublicListSharedVFoldersActionResult:
        raw_list = await self._vfolder_repository.list_shared_vfolder_permissions(
            requester_id=UserID(self._requester().user_id)
        )
        return PublicListSharedVFoldersActionResult(shared=self._to_shared_info(raw_list))

    async def global_list_shared_vfolders(
        self, action: GlobalListSharedVFoldersAction
    ) -> GlobalListSharedVFoldersActionResult:
        raw_list = await self._vfolder_repository.list_shared_vfolder_permissions()
        return GlobalListSharedVFoldersActionResult(shared=self._to_shared_info(raw_list))

    async def update_sharing_status(
        self, action: UpdateVFolderSharingStatusAction
    ) -> UpdateVFolderSharingStatusActionResult:
        await self._vfolder_repository.update_vfolder_sharing_status(
            action.vfolder_uuid,
            action.to_delete,
            action.to_update,
        )
        return UpdateVFolderSharingStatusActionResult()
