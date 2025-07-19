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
from ai.backend.manager.repositories.vfolder.admin_repository import AdminVfolderRepository
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
    _admin_vfolder_repository: AdminVfolderRepository

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        storage_manager: StorageSessionManager,
        vfolder_repository: VfolderRepository,
        admin_vfolder_repository: AdminVfolderRepository,
    ) -> None:
        self._config_provider = config_provider
        self._storage_manager = storage_manager
        self._vfolder_repository = vfolder_repository
        self._admin_vfolder_repository = admin_vfolder_repository

    async def upload_file(
        self, action: CreateUploadSessionAction
    ) -> CreateUploadSessionActionResult:
        # Get VFolder data using repository
        vfolder_data = await self._vfolder_repository.get_by_id(action.vfolder_uuid)
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

        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/upload",
            json={
                "volume": volume_name,
                "vfid": str(vfolder_id),
                "relpath": action.path,
                "size": action.size,
            },
        ) as (client_api_url, storage_resp):
            storage_reply = await storage_resp.json()
        return CreateUploadSessionActionResult(
            vfolder_uuid=action.vfolder_uuid,
            token=storage_reply["token"],
            url=str(client_api_url / "upload"),
        )

    async def download_file(
        self, action: CreateDownloadSessionAction
    ) -> CreateDownloadSessionActionResult:
        # Get VFolder data using repository
        vfolder_data = await self._vfolder_repository.get_by_id(action.vfolder_uuid)
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

        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/download",
            json={
                "volume": volume_name,
                "vfid": str(vfolder_id),
                "relpath": action.path,
                "archive": action.archive,
                "unmanaged_path": vfolder_data.unmanaged_path
                if vfolder_data.unmanaged_path
                else None,
            },
        ) as (client_api_url, storage_resp):
            storage_reply = await storage_resp.json()
        return CreateDownloadSessionActionResult(
            vfolder_uuid=action.vfolder_uuid,
            token=storage_reply["token"],
            url=str(client_api_url / "download"),
        )

    async def list_files(self, action: ListFilesAction) -> ListFilesActionResult:
        # Get user info and check VFolder access using repository
        user_info = await self._vfolder_repository.get_user_info(action.user_uuid)
        if not user_info:
            raise VFolderInvalidParameter("User not found")
        user_role, user_domain_name = user_info

        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        # Check if user has access to the VFolder
        vfolder_list_result = await self._vfolder_repository.list_accessible_vfolders(
            user_id=action.user_uuid,
            user_role=user_role,
            domain_name=user_domain_name,
            allowed_vfolder_types=list(allowed_vfolder_types),
            extra_conditions=None,  # We'll filter by vfolder_uuid below
        )

        # Find the requested vfolder
        vfolder_data = None
        for access_info in vfolder_list_result.vfolders:
            if access_info.vfolder_data.id == action.vfolder_uuid:
                vfolder_data = access_info.vfolder_data
                break

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

        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/list",
            json={
                "volume": volume_name,
                "vfid": str(vfolder_id),
                "relpath": action.path,
            },
        ) as (_, storage_resp):
            result = await storage_resp.json()
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
        vfolder_data = await self._vfolder_repository.get_by_id(action.vfolder_uuid)
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

        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/rename",
            json={
                "volume": volume_name,
                "vfid": str(vfolder_id),
                "relpath": action.target_path,
                "new_name": action.new_name,
            },
        ):
            pass
        return RenameFileActionResult(vfolder_uuid=action.vfolder_uuid)

    async def delete_files(self, action: DeleteFilesAction) -> DeleteFilesActionResult:
        # Get user info and check VFolder access using repository
        user_info = await self._vfolder_repository.get_user_info(action.user_uuid)
        if not user_info:
            raise VFolderInvalidParameter("User not found")
        user_role, user_domain_name = user_info

        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        # Check if user has access to the VFolder
        vfolder_list_result = await self._vfolder_repository.list_accessible_vfolders(
            user_id=action.user_uuid,
            user_role=user_role,
            domain_name=user_domain_name,
            allowed_vfolder_types=list(allowed_vfolder_types),
            extra_conditions=None,  # We'll filter by vfolder_uuid below
        )

        # Find the requested vfolder
        vfolder_data = None
        for access_info in vfolder_list_result.vfolders:
            if access_info.vfolder_data.id == action.vfolder_uuid:
                vfolder_data = access_info.vfolder_data
                break

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

        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/delete",
            json={
                "volume": volume_name,
                "vfid": str(vfolder_id),
                "relpaths": action.files,
                "recursive": action.recursive,
            },
        ):
            pass
        return DeleteFilesActionResult(vfolder_uuid=action.vfolder_uuid)

    async def mkdir(self, action: MkdirAction) -> MkdirActionResult:
        if isinstance(action.path, list) and len(action.path) > 50:
            raise VFolderInvalidParameter("Too many directories specified.")

        # Get VFolder data using repository
        vfolder_data = await self._vfolder_repository.get_by_id(action.vfolder_uuid)
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

        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/mkdir",
            json={
                "volume": volume_name,
                "vfid": str(vfolder_id),
                "relpath": action.path,
                "parents": action.parents,
                "exist_ok": action.exist_ok,
            },
        ) as (_, storage_resp):
            storage_reply = await storage_resp.json()
            results = storage_reply["results"]
        return MkdirActionResult(
            vfolder_uuid=action.vfolder_uuid,
            results=results,
            storage_resp_status=storage_resp.status,
        )
