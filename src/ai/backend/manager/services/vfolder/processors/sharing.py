from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.vfolder.actions.sharing import (
    ListSharedVFoldersAction,
    ListSharedVFoldersActionResult,
    ShareVFolderAction,
    ShareVFolderActionResult,
    UnshareVFolderAction,
    UnshareVFolderActionResult,
    UpdateVFolderSharingStatusAction,
    UpdateVFolderSharingStatusActionResult,
)
from ai.backend.manager.services.vfolder.services.sharing import VFolderSharingService


class VFolderSharingProcessors(AbstractProcessorPackage):
    share: ActionProcessor[ShareVFolderAction, ShareVFolderActionResult]
    unshare: ActionProcessor[UnshareVFolderAction, UnshareVFolderActionResult]
    list_shared: ActionProcessor[ListSharedVFoldersAction, ListSharedVFoldersActionResult]
    update_sharing_status: ActionProcessor[
        UpdateVFolderSharingStatusAction, UpdateVFolderSharingStatusActionResult
    ]

    def __init__(
        self, service: VFolderSharingService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.share = ActionProcessor(service.share, action_monitors)
        self.unshare = ActionProcessor(service.unshare, action_monitors)
        self.list_shared = ActionProcessor(service.list_shared_vfolders, action_monitors)
        self.update_sharing_status = ActionProcessor(service.update_sharing_status, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ShareVFolderAction.spec(),
            UnshareVFolderAction.spec(),
            ListSharedVFoldersAction.spec(),
            UpdateVFolderSharingStatusAction.spec(),
        ]
