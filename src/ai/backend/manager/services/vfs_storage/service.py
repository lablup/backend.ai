import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.vfs_storage.actions.create import (
    CreateVFSStorageAction,
    CreateVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.delete import (
    DeleteVFSStorageAction,
    DeleteVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.get import (
    GetVFSStorageAction,
    GetVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.get_quota_scope import (
    GetQuotaScopeAction,
    GetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.list import (
    ListVFSStorageAction,
    ListVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.search import (
    SearchVFSStoragesAction,
    SearchVFSStoragesActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.search_quota_scopes import (
    QuotaScopeInfo,
    SearchQuotaScopesAction,
    SearchQuotaScopesActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.set_quota_scope import (
    SetQuotaScopeAction,
    SetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.unset_quota_scope import (
    UnsetQuotaScopeAction,
    UnsetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.update import (
    UpdateVFSStorageAction,
    UpdateVFSStorageActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFSStorageService:
    _vfs_storage_repository: VFSStorageRepository
    _storage_manager: StorageSessionManager | None

    def __init__(
        self,
        vfs_storage_repository: VFSStorageRepository,
        storage_manager: StorageSessionManager | None = None,
    ) -> None:
        self._vfs_storage_repository = vfs_storage_repository
        self._storage_manager = storage_manager

    async def create(self, action: CreateVFSStorageAction) -> CreateVFSStorageActionResult:
        """
        Create a new VFS storage.
        """
        log.info("Creating VFS storage with data: {}", action.creator)
        storage_data = await self._vfs_storage_repository.create(
            action.creator, action.meta_creator
        )
        return CreateVFSStorageActionResult(result=storage_data)

    async def update(self, action: UpdateVFSStorageAction) -> UpdateVFSStorageActionResult:
        """
        Update an existing VFS storage.
        """
        log.info("Updating VFS storage with id: {}", action.updater.pk_value)
        storage_data = await self._vfs_storage_repository.update(action.updater)
        return UpdateVFSStorageActionResult(result=storage_data)

    async def delete(self, action: DeleteVFSStorageAction) -> DeleteVFSStorageActionResult:
        """
        Delete an existing VFS storage.
        """
        log.info("Deleting VFS storage with id: {}", action.storage_id)
        storage_data = await self._vfs_storage_repository.delete(action.storage_id)
        return DeleteVFSStorageActionResult(deleted_storage_id=storage_data)

    async def get(self, action: GetVFSStorageAction) -> GetVFSStorageActionResult:
        """
        Get an existing VFS storage by ID.
        """
        log.info("Getting VFS storage with id: {}", action.storage_id)
        if action.storage_id:
            storage_data = await self._vfs_storage_repository.get_by_id(action.storage_id)
        elif action.storage_name:
            storage_data = await self._vfs_storage_repository.get_by_name(action.storage_name)
        else:
            raise GenericBadRequest("Either storage_id or storage_name must be provided")

        return GetVFSStorageActionResult(result=storage_data)

    async def list(self, _action: ListVFSStorageAction) -> ListVFSStorageActionResult:
        """
        List all VFS storages.
        """
        log.info("Listing VFS storages")
        storage_data_list = await self._vfs_storage_repository.list_vfs_storages()
        return ListVFSStorageActionResult(data=storage_data_list)

    async def search(self, action: SearchVFSStoragesAction) -> SearchVFSStoragesActionResult:
        """
        Search VFS storages with pagination and filtering.
        """
        log.info("Searching VFS storages with querier: {}", action.querier)
        result = await self._vfs_storage_repository.search(action.querier)
        return SearchVFSStoragesActionResult(
            storages=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    def _ensure_storage_manager(self) -> StorageSessionManager:
        if self._storage_manager is None:
            raise RuntimeError("Storage manager is not configured")
        return self._storage_manager

    async def get_quota_scope(self, action: GetQuotaScopeAction) -> GetQuotaScopeActionResult:
        storage_manager = self._ensure_storage_manager()
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(
            action.storage_host_name
        )
        manager_client = storage_manager.get_manager_facing_client(proxy_name)
        quota_config = await manager_client.get_quota_scope(volume_name, action.quota_scope_id)
        usage_bytes = quota_config.get("used_bytes")
        if usage_bytes is not None and usage_bytes < 0:
            usage_bytes = None
        return GetQuotaScopeActionResult(
            quota_scope_id=action.quota_scope_id,
            storage_host_name=action.storage_host_name,
            usage_bytes=usage_bytes,
            usage_count=None,
            hard_limit_bytes=quota_config.get("limit_bytes") or None,
        )

    async def search_quota_scopes(
        self, _action: SearchQuotaScopesAction
    ) -> SearchQuotaScopesActionResult:
        storage_manager = self._ensure_storage_manager()
        all_volumes = await storage_manager.get_all_volumes()
        quota_scopes: list[QuotaScopeInfo] = []
        for host, _volume_info in all_volumes:
            proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(host)
            manager_client = storage_manager.get_manager_facing_client(proxy_name)
            try:
                quota_config = await manager_client.get_quota_scope(volume_name, "")
                usage_bytes = quota_config.get("used_bytes")
                if usage_bytes is not None and usage_bytes < 0:
                    usage_bytes = None
                quota_scopes.append(
                    QuotaScopeInfo(
                        quota_scope_id="",
                        storage_host_name=host,
                        usage_bytes=usage_bytes,
                        usage_count=None,
                        hard_limit_bytes=quota_config.get("limit_bytes") or None,
                    )
                )
            except Exception:
                pass
        return SearchQuotaScopesActionResult(quota_scopes=quota_scopes)

    async def set_quota_scope(self, action: SetQuotaScopeAction) -> SetQuotaScopeActionResult:
        storage_manager = self._ensure_storage_manager()
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(
            action.storage_host_name
        )
        manager_client = storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.update_quota_scope(
            volume_name, action.quota_scope_id, action.hard_limit_bytes
        )
        quota_config = await manager_client.get_quota_scope(volume_name, action.quota_scope_id)
        usage_bytes = quota_config.get("used_bytes")
        if usage_bytes is not None and usage_bytes < 0:
            usage_bytes = None
        return SetQuotaScopeActionResult(
            quota_scope_id=action.quota_scope_id,
            storage_host_name=action.storage_host_name,
            usage_bytes=usage_bytes,
            usage_count=None,
            hard_limit_bytes=quota_config.get("limit_bytes") or None,
        )

    async def unset_quota_scope(self, action: UnsetQuotaScopeAction) -> UnsetQuotaScopeActionResult:
        storage_manager = self._ensure_storage_manager()
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(
            action.storage_host_name
        )
        manager_client = storage_manager.get_manager_facing_client(proxy_name)
        await manager_client.delete_quota_scope_quota(volume_name, action.quota_scope_id)
        return UnsetQuotaScopeActionResult(
            quota_scope_id=action.quota_scope_id,
            storage_host_name=action.storage_host_name,
        )
