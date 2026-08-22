import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.vfs_storage.actions.get_quota_scope import (
    GetQuotaScopeAction,
    GetQuotaScopeActionResult,
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
