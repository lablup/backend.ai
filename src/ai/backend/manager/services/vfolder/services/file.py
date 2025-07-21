from ai.backend.common.types import (
    VFolderHostPermission,
    VFolderID,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.storage import VFolderInvalidParameter
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.vfolder import (
    is_unmanaged,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository

from ..actions.file import (
    CreateDownloadSessionAction,
    CreateDownloadSessionActionResult,
    CreateUploadSessionAction,
    CreateUploadSessionActionResult,
    DeleteFilesAction,
    DeleteFilesActionResult,
    ListFilesAction,
    ListFilesActionResult,
    MkdirAction,
    MkdirActionResult,
    RenameFileAction,
    RenameFileActionResult,
)
from ..types import FileInfo


class VFolderFileService:
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _vfolder_repository: VfolderRepository
    _user_repository: UserRepository

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        storage_manager: StorageSessionManager,
        vfolder_repository: VfolderRepository,
        user_repository: UserRepository,
    ) -> None:
        self._config_provider = config_provider
        self._storage_manager = storage_manager
        self._vfolder_repository = vfolder_repository
        self._user_repository = user_repository

    async def upload_file(
        self, action: CreateUploadSessionAction
    ) -> CreateUploadSessionActionResult:
        # Get VFolder data using repository
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        if not vfolder_data:
            raise VFolderInvalidParameter("VFolder not found")

        # Check host permissions
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        await self._vfolder_repository.ensure_host_permission_allowed(
            vfolder_data.host,
            permission=VFolderHostPermission.UPLOAD_FILE,
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=action.user_uuid,
            resource_policy=action.keypair_resource_policy,
            domain_name=vfolder_data.domain_name,
        )

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_data.host, is_unmanaged(vfolder_data.unmanaged_path)
        )

        # Create VFolderID from data
        vfolder_id = VFolderID(
            quota_scope_id=vfolder_data.quota_scope_id,
            folder_id=vfolder_data.id,
        )

        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        storage_reply = await manager_client.upload_file(
            volume_name,
            str(vfolder_id),
            action.path,
            action.size,
        )
        client_api_url = self._storage_manager.get_client_api_url(proxy_name)
        return CreateUploadSessionActionResult(
            vfolder_uuid=action.vfolder_uuid,
            token=storage_reply["token"],
            url=str(client_api_url / "upload"),
        )

    async def download_file(
        self, action: CreateDownloadSessionAction
    ) -> CreateDownloadSessionActionResult:
        # Get VFolder data using repository
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        if not vfolder_data:
            raise VFolderInvalidParameter("VFolder not found")

        # Check host permissions
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        await self._vfolder_repository.ensure_host_permission_allowed(
            vfolder_data.host,
            permission=VFolderHostPermission.DOWNLOAD_FILE,
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=action.user_uuid,
            resource_policy=action.keypair_resource_policy,
            domain_name=vfolder_data.domain_name,
        )

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_data.host, is_unmanaged(vfolder_data.unmanaged_path)
        )

        # Create VFolderID from data
        vfolder_id = VFolderID(
            quota_scope_id=vfolder_data.quota_scope_id,
            folder_id=vfolder_data.id,
        )

        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        # For download, we need to handle the request differently as it includes extra params
        storage_reply = await manager_client.download_file(
            volume=volume_name,
            vfid=str(vfolder_id),
            relpath=action.path,
            archive=action.archive,
            unmanaged_path=vfolder_data.unmanaged_path,
        )
        client_api_url = self._storage_manager.get_client_api_url(proxy_name)
        return CreateDownloadSessionActionResult(
            vfolder_uuid=action.vfolder_uuid,
            token=storage_reply["token"],
            url=str(client_api_url / "download"),
        )

    async def list_files(self, action: ListFilesAction) -> ListFilesActionResult:
        # Get user info and check VFolder access using repository
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_data.host, is_unmanaged(vfolder_data.unmanaged_path)
        )

        # Create VFolderID from data
        vfolder_id = VFolderID(
            quota_scope_id=vfolder_data.quota_scope_id,
            folder_id=vfolder_data.id,
        )

        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        result = await manager_client.list_files(
            volume_name,
            str(vfolder_id),
            action.path,
        )
        return ListFilesActionResult(
            vfolder_uuid=action.vfolder_uuid,
            files=[
                FileInfo(
                    name=item["name"],
                    type=item["type"],
                    size=item["stat"]["size"],
                    mode=item["stat"]["mode"],
                    created=item["stat"]["created"],
                    modified=item["stat"]["modified"],
                )
                for item in result["items"]
            ],
        )

    async def rename_file(self, action: RenameFileAction) -> RenameFileActionResult:
        # Get VFolder data using repository
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        if not vfolder_data:
            raise VFolderInvalidParameter("VFolder not found")

        # Check host permissions
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        await self._vfolder_repository.ensure_host_permission_allowed(
            vfolder_data.host,
            permission=VFolderHostPermission.MODIFY,
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=action.user_uuid,
            resource_policy=action.keypair_resource_policy,
            domain_name=vfolder_data.domain_name,
        )

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_data.host, is_unmanaged(vfolder_data.unmanaged_path)
        )

        # Create VFolderID from data
        vfolder_id = VFolderID(
            quota_scope_id=vfolder_data.quota_scope_id,
            folder_id=vfolder_data.id,
        )

        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.rename_file(
            volume_name,
            str(vfolder_id),
            action.target_path,
            action.new_name,
        )
        return RenameFileActionResult(vfolder_uuid=action.vfolder_uuid)

    async def delete_files(self, action: DeleteFilesAction) -> DeleteFilesActionResult:
        # Get user info and check VFolder access using repository
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )

        if not vfolder_data:
            raise VFolderInvalidParameter("The specified vfolder is not accessible.")

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_data.host, is_unmanaged(vfolder_data.unmanaged_path)
        )

        # Create VFolderID from data
        vfolder_id = VFolderID(
            quota_scope_id=vfolder_data.quota_scope_id,
            folder_id=vfolder_data.id,
        )

        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.delete_files(
            volume_name,
            str(vfolder_id),
            action.files,
            action.recursive,
        )
        return DeleteFilesActionResult(vfolder_uuid=action.vfolder_uuid)

    async def mkdir(self, action: MkdirAction) -> MkdirActionResult:
        if isinstance(action.path, list) and len(action.path) > 50:
            raise VFolderInvalidParameter("Too many directories specified.")

        # Get VFolder data using repository
        user = await self._user_repository.get_user_by_uuid(action.user_id)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        if not vfolder_data:
            raise VFolderInvalidParameter("VFolder not found")

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_data.host, is_unmanaged(vfolder_data.unmanaged_path)
        )

        # Create VFolderID from data
        vfolder_id = VFolderID(
            quota_scope_id=vfolder_data.quota_scope_id,
            folder_id=vfolder_data.id,
        )

        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)
        storage_reply = await manager_client.mkdir(
            volume=volume_name,
            vfid=str(vfolder_id),
            relpath=action.path,
            exist_ok=action.exist_ok,
            parents=action.parents,
        )
        results = storage_reply["results"]
        return MkdirActionResult(
            vfolder_uuid=action.vfolder_uuid,
            results=results,
            storage_resp_status=200,
        )
