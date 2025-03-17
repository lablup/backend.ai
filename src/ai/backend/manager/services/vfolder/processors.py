from ai.backend.manager.actions.processor import ActionProcessor

from .actions import (
    ChangeOwnershipAction,
    ChangeOwnershipActionResult,
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteFilesAction,
    DeleteFilesActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    DownloadFileAction,
    DownloadFileActionResult,
    InviteVFolderAction,
    InviteVFolderActionResult,
    LeaveInvitedVFolderAction,
    LeaveInvitedVFolderActionResult,
    ListFilesAction,
    ListFilesActionResult,
    ListInvitationAction,
    ListInvitationActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MkdirAction,
    MkdirActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    PurgeVFolderAction,
    PurgeVFolderActionResult,
    ReceiveInvitationAction,
    ReceiveInvitationActionResult,
    RenameFileAction,
    RenameFileActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateInvitationAction,
    UpdateInvitationActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
    UploadFileAction,
    UploadFileActionResult,
)
from .service import VFolderService


class VFolderProcessors:
    create_vfolder = ActionProcessor[CreateVFolderAction, CreateVFolderActionResult]
    list_vfolder = ActionProcessor[ListVFolderAction, ListVFolderActionResult]
    upload_file = ActionProcessor[UploadFileAction, UploadFileActionResult]
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

    # Invite operations
    invite_vfolder = ActionProcessor[InviteVFolderAction, InviteVFolderActionResult]
    receive_invitation = ActionProcessor[ReceiveInvitationAction, ReceiveInvitationActionResult]
    update_invitation = ActionProcessor[UpdateInvitationAction, UpdateInvitationActionResult]
    list_invitation = ActionProcessor[ListInvitationAction, ListInvitationActionResult]
    leave_invited_vfolder = ActionProcessor[
        LeaveInvitedVFolderAction, LeaveInvitedVFolderActionResult
    ]

    # File operations
    list_files = ActionProcessor[ListFilesAction, ListFilesActionResult]
    download_file = ActionProcessor[DownloadFileAction, DownloadFileActionResult]
    mkdir = ActionProcessor[MkdirAction, MkdirActionResult]
    rename_file = ActionProcessor[RenameFileAction, RenameFileActionResult]
    delete_files = ActionProcessor[DeleteFilesAction, DeleteFilesActionResult]

    def __init__(self, service: VFolderService) -> None:
        self.create_vfolder = ActionProcessor(service.create)
        self.list_vfolder = ActionProcessor(service.list)
        self.update_vfolder_attribute = ActionProcessor(service.update_attribute)
        self.change_ownership = ActionProcessor(service.change_ownership)
        self.move_to_trash_vfolder = ActionProcessor(service.move_to_trash)
        self.restore_vfolder_from_trash = ActionProcessor(service.restore)
        self.delete_forever_vfolder = ActionProcessor(service.delete_forever)
        self.purge_vfolder = ActionProcessor(service.purge)
        self.clone_vfolder = ActionProcessor(service.clone)

        # Invite
        self.invite_vfolder = ActionProcessor(service.invite)
        self.receive_invitation = ActionProcessor(service.receive_invitation)
        self.update_invitation = ActionProcessor(service.update_invitation)
        self.list_invitation = ActionProcessor(service.list_invitation)
        self.leave_invited_vfolder = ActionProcessor(service.leave_invited_vfolder)

        # File operations
        self.list_files = ActionProcessor(service.list_files)
        self.download_file = ActionProcessor(service.download_file)
        self.upload_file = ActionProcessor(service.upload_file)
        self.mkdir = ActionProcessor(service.mkdir)
        self.rename_file = ActionProcessor(service.rename_file)
        self.delete_files = ActionProcessor(service.delete_files)
