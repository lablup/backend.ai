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
from ai.backend.manager.services.vfs_storage.actions.list import (
    ListVFSStorageAction,
    ListVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.search import (
    SearchVFSStoragesAction,
    SearchVFSStoragesActionResult,
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

    def __init__(self, service: VFSStorageService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.get = ActionProcessor(service.get, action_monitors)
        self.list_storages = ActionProcessor(service.list, action_monitors)
        self.search_vfs_storages = ActionProcessor(service.search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateVFSStorageAction.spec(),
            UpdateVFSStorageAction.spec(),
            DeleteVFSStorageAction.spec(),
            GetVFSStorageAction.spec(),
            ListVFSStorageAction.spec(),
            SearchVFSStoragesAction.spec(),
        ]
