from typing import (
    cast,
)

import sqlalchemy as sa

from ai.backend.common.types import (
    VFolderHostPermission,
    VFolderID,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderRow,
    ensure_host_permission_allowed,
    is_unmanaged,
    query_accessible_vfolders,
)

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
from ..exceptions import VFolderInvalidParameter
from ..types import FileInfo


class VFolderFileService:
    _db: ExtendedAsyncSAEngine
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        config_provider: ManagerConfigProvider,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._db = db
        self._config_provider = config_provider
        self._storage_manager = storage_manager

    async def upload_file(
        self, action: CreateUploadSessionAction
    ) -> CreateUploadSessionActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with self._db.begin_readonly_session() as db_session:
            query_vfolder = sa.select(VFolderRow).where(VFolderRow.id == action.vfolder_uuid)
            vfolder_row = await db_session.scalar(query_vfolder)
            vfolder_row = cast(VFolderRow, vfolder_row)
            await ensure_host_permission_allowed(
                db_session.bind,
                vfolder_row.host,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=action.user_uuid,
                resource_policy=action.keypair_resource_policy,
                domain_name=vfolder_row.domain_name,
                permission=VFolderHostPermission.UPLOAD_FILE,
            )
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_row.host, is_unmanaged(vfolder_row.unmanaged_path)
        )
        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/upload",
            json={
                "volume": volume_name,
                "vfid": str(VFolderID.from_row(vfolder_row)),
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
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with self._db.begin_readonly_session() as db_session:
            query_vfolder = sa.select(VFolderRow).where(VFolderRow.id == action.vfolder_uuid)
            vfolder_row = await db_session.scalar(query_vfolder)
            vfolder_row = cast(VFolderRow, vfolder_row)
            unmanaged_path = vfolder_row.unmanaged_path
            await ensure_host_permission_allowed(
                db_session.bind,
                vfolder_row.host,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=action.user_uuid,
                resource_policy=action.keypair_resource_policy,
                domain_name=vfolder_row.domain_name,
                permission=VFolderHostPermission.DOWNLOAD_FILE,
            )
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_row.host, is_unmanaged(unmanaged_path)
        )
        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/download",
            json={
                "volume": volume_name,
                "vfid": str(VFolderID.from_row(vfolder_row)),
                "relpath": action.path,
                "archive": action.archive,
                "unmanaged_path": unmanaged_path if unmanaged_path else None,
            },
        ) as (client_api_url, storage_resp):
            storage_reply = await storage_resp.json()
        return CreateDownloadSessionActionResult(
            vfolder_uuid=action.vfolder_uuid,
            token=storage_reply["token"],
            url=str(client_api_url / "download"),
        )

    async def list_files(self, action: ListFilesAction) -> ListFilesActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with self._db.begin_session() as db_session:
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            requester_user_row = cast(UserRow, requester_user_row)
            vfolder_dicts = await query_accessible_vfolders(
                db_session.bind,
                action.user_uuid,
                allow_privileged_access=True,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
                extra_vf_conds=(VFolderRow.id == action.vfolder_uuid),
            )
            if not vfolder_dicts:
                raise VFolderInvalidParameter("The specified vfolder is not accessible.")
            vfolder_row = vfolder_dicts[0]
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_row["host"], is_unmanaged(vfolder_row["unmanaged_path"])
        )
        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/list",
            json={
                "volume": volume_name,
                "vfid": str(VFolderID(vfolder_row["quota_scope_id"], vfolder_row["id"])),
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
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with self._db.begin_readonly_session() as db_session:
            query_vfolder = sa.select(VFolderRow).where(VFolderRow.id == action.vfolder_uuid)
            vfolder_row = await db_session.scalar(query_vfolder)
            vfolder_row = cast(VFolderRow, vfolder_row)
            await ensure_host_permission_allowed(
                db_session.bind,
                vfolder_row.host,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=action.user_uuid,
                resource_policy=action.keypair_resource_policy,
                domain_name=vfolder_row.domain_name,
                permission=VFolderHostPermission.MODIFY,
            )
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_row.host, is_unmanaged(vfolder_row.unmanaged_path)
        )
        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/rename",
            json={
                "volume": volume_name,
                "vfid": str(VFolderID.from_row(vfolder_row)),
                "relpath": action.target_path,
                "new_name": action.new_name,
            },
        ):
            pass
        return RenameFileActionResult(vfolder_uuid=action.vfolder_uuid)

    async def delete_files(self, action: DeleteFilesAction) -> DeleteFilesActionResult:
        allowed_vfolder_types = (
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )
        async with self._db.begin_session() as db_session:
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            requester_user_row = cast(UserRow, requester_user_row)
            vfolder_dicts = await query_accessible_vfolders(
                db_session.bind,
                action.user_uuid,
                allow_privileged_access=True,
                user_role=requester_user_row.role,
                allowed_vfolder_types=allowed_vfolder_types,
                domain_name=requester_user_row.domain_name,
                extra_vf_conds=(VFolderRow.id == action.vfolder_uuid),
            )
            if not vfolder_dicts:
                raise VFolderInvalidParameter("The specified vfolder is not accessible.")
            vfolder_row = vfolder_dicts[0]
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_row["host"], is_unmanaged(vfolder_row["unmanaged_path"])
        )
        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/delete",
            json={
                "volume": volume_name,
                "vfid": str(VFolderID(vfolder_row["quota_scope_id"], vfolder_row["id"])),
                "relpaths": action.files,
                "recursive": action.recursive,
            },
        ):
            pass
        return DeleteFilesActionResult(vfolder_uuid=action.vfolder_uuid)

    async def mkdir(self, action: MkdirAction) -> MkdirActionResult:
        if isinstance(action.path, list) and len(action.path) > 50:
            raise VFolderInvalidParameter("Too many directories specified.")
        async with self._db.begin_readonly_session() as db_session:
            query_vfolder = sa.select(VFolderRow).where(VFolderRow.id == action.vfolder_uuid)
            vfolder_row = await db_session.scalar(query_vfolder)
            vfolder_row = cast(VFolderRow, vfolder_row)
        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            vfolder_row.host, is_unmanaged(vfolder_row.unmanaged_path)
        )
        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/mkdir",
            json={
                "volume": volume_name,
                "vfid": str(VFolderID.from_row(vfolder_row)),
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
