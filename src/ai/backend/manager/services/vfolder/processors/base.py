from ai.backend.manager.actions.processor import ActionProcessor

from ..actions.base import (
    ChangeOwnershipAction,
    ChangeOwnershipActionResult,
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    PurgeVFolderAction,
    PurgeVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
)
from ..services.base import VFolderService


class VFolderBaseProcessors:
    create_vfolder = ActionProcessor[CreateVFolderAction, CreateVFolderActionResult]
    list_vfolder = ActionProcessor[ListVFolderAction, ListVFolderActionResult]
    update_vfolder_attribute = ActionProcessor[
        UpdateVFolderAttributeAction, UpdateVFolderAttributeActionResult
    ]
    change_ownership = ActionProcessor[ChangeOwnershipAction, ChangeOwnershipActionResult]
    move_to_trash_vfolder = ActionProcessor[
        MoveToTrashVFolderAction, MoveToTrashVFolderActionResult
    ]
    restore_vfolder_from_trash = ActionProcessor[
        RestoreVFolderFromTrashAction, RestoreVFolderFromTrashActionResult
    ]
    delete_forever_vfolder = ActionProcessor[
        DeleteForeverVFolderAction, DeleteForeverVFolderActionResult
    ]
    purge_vfolder = ActionProcessor[PurgeVFolderAction, PurgeVFolderActionResult]
    clone_vfolder = ActionProcessor[CloneVFolderAction, CloneVFolderActionResult]

    def __init__(self, service: VFolderService):
        self.create_vfolder = ActionProcessor(service.create)
        self.list_vfolder = ActionProcessor(service.list)
        self.update_vfolder_attribute = ActionProcessor(service.update_attribute)
        self.change_ownership = ActionProcessor(service.change_ownership)
        self.move_to_trash_vfolder = ActionProcessor(service.move_to_trash)
        self.restore_vfolder_from_trash = ActionProcessor(service.restore)
        self.delete_forever_vfolder = ActionProcessor(service.delete_forever)
        self.purge_vfolder = ActionProcessor(service.purge)
        self.clone_vfolder = ActionProcessor(service.clone)
