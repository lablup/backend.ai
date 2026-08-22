from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import PublicActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.services.vfolder.actions.sharing import (
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
)
from ai.backend.manager.services.vfolder.services.sharing import VFolderSharingService


class VFolderSharingProcessors:
    share: SingleEntityActionProcessor[ShareVFolderAction, ShareVFolderActionResult]
    unshare: SingleEntityActionProcessor[UnshareVFolderAction, UnshareVFolderActionResult]
    list_shared: SingleEntityActionProcessor[
        ListSharedVFoldersAction, ListSharedVFoldersActionResult
    ]
    public_list_shared: PublicActionProcessor[
        PublicListSharedVFoldersAction, PublicListSharedVFoldersActionResult
    ]
    update_sharing_status: SingleEntityActionProcessor[
        UpdateVFolderSharingStatusAction, UpdateVFolderSharingStatusActionResult
    ]

    def __init__(self, group: ProcessorGroup[VFolderData], service: VFolderSharingService) -> None:
        self.share = group.single_entity(ShareVFolderAction, service.share)
        self.unshare = group.single_entity(UnshareVFolderAction, service.unshare)
        self.list_shared = group.single_entity(
            ListSharedVFoldersAction, service.list_shared_vfolders
        )
        self.public_list_shared = group.public(
            PublicListSharedVFoldersAction, service.public_list_shared_vfolders
        )
        self.update_sharing_status = group.single_entity(
            UpdateVFolderSharingStatusAction, service.update_sharing_status
        )
