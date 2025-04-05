from ai.backend.manager.actions.processor import ActionProcessor

from ..actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ForceDeleteVFolderAction,
    ForceDeleteVFolderActionResult,
    GetVFolderAction,
    GetVFolderActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
)
from ..services.base import VFolderService


class VFolderBaseProcessors:
    create_vfolder: ActionProcessor[CreateVFolderAction, CreateVFolderActionResult]
    get_vfolder: ActionProcessor[GetVFolderAction, GetVFolderActionResult]
    list_vfolder: ActionProcessor[ListVFolderAction, ListVFolderActionResult]
    update_vfolder_attribute: ActionProcessor[
        UpdateVFolderAttributeAction, UpdateVFolderAttributeActionResult
    ]
    move_to_trash_vfolder: ActionProcessor[MoveToTrashVFolderAction, MoveToTrashVFolderActionResult]
    restore_vfolder_from_trash: ActionProcessor[
        RestoreVFolderFromTrashAction, RestoreVFolderFromTrashActionResult
    ]
    delete_forever_vfolder: ActionProcessor[
        DeleteForeverVFolderAction, DeleteForeverVFolderActionResult
    ]
    force_delete_vfolder: ActionProcessor[ForceDeleteVFolderAction, ForceDeleteVFolderActionResult]
    clone_vfolder: ActionProcessor[CloneVFolderAction, CloneVFolderActionResult]

    def __init__(self, service: VFolderService):
        self.create_vfolder = ActionProcessor(service.create)
        self.get_vfolder = ActionProcessor(service.get)
        self.list_vfolder = ActionProcessor(service.list)
        self.update_vfolder_attribute = ActionProcessor(service.update_attribute)
        self.move_to_trash_vfolder = ActionProcessor(service.move_to_trash)
        self.restore_vfolder_from_trash = ActionProcessor(service.restore)
        self.delete_forever_vfolder = ActionProcessor(service.delete_forever)
        self.force_delete_vfolder = ActionProcessor(service.force_delete)
        self.clone_vfolder = ActionProcessor(service.clone)
