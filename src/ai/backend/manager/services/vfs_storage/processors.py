from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.services.vfs_storage.actions.create import CreateVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.get import GetVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.get_quota_scope import (
    GetQuotaScopeAction,
    GetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.list import ListVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.purge import PurgeVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.resolve_by_name import (
    ResolveVFSStorageByNameAction,
)
from ai.backend.manager.services.vfs_storage.actions.search import SearchVFSStoragesAction
from ai.backend.manager.services.vfs_storage.actions.search_quota_scopes import (
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
from ai.backend.manager.services.vfs_storage.actions.update import UpdateVFSStorageAction
from ai.backend.manager.services.vfs_storage.service import VFSStorageService


class VFSStorageProcessors:
    """The registry CRUD runs against ops; the quota-scope paths keep a service."""

    global_create: GlobalActionProcessor[
        CreateVFSStorageAction, CreatedEntityOpsResult[VFSStorageData]
    ]
    global_update: GlobalActionProcessor[UpdateVFSStorageAction, EntityOpsResult[VFSStorageData]]
    global_purge: GlobalActionProcessor[PurgeVFSStorageAction, EntityOpsResult[VFSStorageData]]
    global_get: GlobalActionProcessor[GetVFSStorageAction, EntityOpsResult[VFSStorageData]]
    lookup: LookupActionProcessor[ResolveVFSStorageByNameAction, LookupOpsResult[VFSStorageData]]
    global_list_storages: GlobalActionProcessor[
        ListVFSStorageAction, BatchOpsResult[VFSStorageData]
    ]
    global_search_vfs_storages: GlobalActionProcessor[
        SearchVFSStoragesAction, BatchOpsResult[VFSStorageData]
    ]
    global_get_quota_scope: GlobalActionProcessor[GetQuotaScopeAction, GetQuotaScopeActionResult]
    global_search_quota_scopes: GlobalActionProcessor[
        SearchQuotaScopesAction, SearchQuotaScopesActionResult
    ]
    global_set_quota_scope: GlobalActionProcessor[SetQuotaScopeAction, SetQuotaScopeActionResult]
    global_unset_quota_scope: GlobalActionProcessor[
        UnsetQuotaScopeAction, UnsetQuotaScopeActionResult
    ]

    _service: VFSStorageService

    def __init__(
        self,
        service: VFSStorageService,
        group: ProcessorGroup[VFSStorageData],
    ) -> None:
        self._service = service
        self.global_create = group.global_create_ops(CreateVFSStorageAction)
        self.global_update = group.global_update_ops(UpdateVFSStorageAction)
        self.global_purge = group.global_purge_ops(PurgeVFSStorageAction)
        self.global_get = group.global_get_ops(GetVFSStorageAction)
        self.lookup = group.lookup_ops(ResolveVFSStorageByNameAction)
        self.global_list_storages = group.global_search_ops(ListVFSStorageAction)
        self.global_search_vfs_storages = group.global_search_ops(SearchVFSStoragesAction)
        self.global_get_quota_scope = group.global_scope(
            GetQuotaScopeAction, service.get_quota_scope
        )
        self.global_search_quota_scopes = group.global_scope(
            SearchQuotaScopesAction, service.search_quota_scopes
        )
        self.global_set_quota_scope = group.global_scope(
            SetQuotaScopeAction, service.set_quota_scope
        )
        self.global_unset_quota_scope = group.global_scope(
            UnsetQuotaScopeAction, service.unset_quota_scope
        )

    def get_manager_facing_client(self, proxy_name: str) -> StorageProxyManagerFacingClient:
        """Get a storage proxy client for the given proxy name.

        Delegates to the underlying service's storage_manager.
        """
        storage_manager = self._service._ensure_storage_manager()
        return storage_manager.get_manager_facing_client(proxy_name)
