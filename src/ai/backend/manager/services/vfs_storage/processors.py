from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
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
from ai.backend.manager.services.vfs_storage.service import VFSStorageService


class VFSStorageProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateVFSStorageAction, CreateVFSStorageActionResult]
    update: ActionProcessor[UpdateVFSStorageAction, UpdateVFSStorageActionResult]
    delete: ActionProcessor[DeleteVFSStorageAction, DeleteVFSStorageActionResult]
    get: ActionProcessor[GetVFSStorageAction, GetVFSStorageActionResult]
    list_storages: ActionProcessor[ListVFSStorageAction, ListVFSStorageActionResult]
    search_vfs_storages: ActionProcessor[SearchVFSStoragesAction, SearchVFSStoragesActionResult]
    get_quota_scope: ActionProcessor[GetQuotaScopeAction, GetQuotaScopeActionResult]
    search_quota_scopes: ActionProcessor[SearchQuotaScopesAction, SearchQuotaScopesActionResult]
    set_quota_scope: ActionProcessor[SetQuotaScopeAction, SetQuotaScopeActionResult]
    unset_quota_scope: ActionProcessor[UnsetQuotaScopeAction, UnsetQuotaScopeActionResult]

    def __init__(self, service: VFSStorageService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.get = ActionProcessor(service.get, action_monitors)
        self.list_storages = ActionProcessor(service.list, action_monitors)
        self.search_vfs_storages = ActionProcessor(service.search, action_monitors)
        self.get_quota_scope = ActionProcessor(service.get_quota_scope, action_monitors)
        self.search_quota_scopes = ActionProcessor(service.search_quota_scopes, action_monitors)
        self.set_quota_scope = ActionProcessor(service.set_quota_scope, action_monitors)
        self.unset_quota_scope = ActionProcessor(service.unset_quota_scope, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateVFSStorageAction.spec(),
            UpdateVFSStorageAction.spec(),
            DeleteVFSStorageAction.spec(),
            GetVFSStorageAction.spec(),
            ListVFSStorageAction.spec(),
            SearchVFSStoragesAction.spec(),
            GetQuotaScopeAction.spec(),
            SearchQuotaScopesAction.spec(),
            SetQuotaScopeAction.spec(),
            UnsetQuotaScopeAction.spec(),
        ]
