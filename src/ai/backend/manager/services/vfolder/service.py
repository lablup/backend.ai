from dataclasses import dataclass

from ...models.utils import ExtendedAsyncSAEngine
from ...registry import AgentRegistry
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


@dataclass
class ServiceInitParameter:
    db: ExtendedAsyncSAEngine
    registry: AgentRegistry


class VFolderService:
    _db: ExtendedAsyncSAEngine
    _registry: AgentRegistry

    def __init__(self, parameter: ServiceInitParameter) -> None:
        self._db = parameter.db
        self._registry = parameter.registry

    async def create(self, action: CreateVFolderAction) -> CreateVFolderActionResult:
        pass

    async def update_attribute(
        self, action: UpdateVFolderAttributeAction
    ) -> UpdateVFolderAttributeActionResult:
        pass

    async def change_ownership(self, action: ChangeOwnershipAction) -> ChangeOwnershipActionResult:
        pass

    async def list(self, action: ListVFolderAction) -> ListVFolderActionResult:
        pass

    async def move_to_trash(
        self, action: MoveToTrashVFolderAction
    ) -> MoveToTrashVFolderActionResult:
        pass

    async def restore(
        self, action: RestoreVFolderFromTrashAction
    ) -> RestoreVFolderFromTrashActionResult:
        pass

    async def delete_forever(
        self, action: DeleteForeverVFolderAction
    ) -> DeleteForeverVFolderActionResult:
        pass

    async def purge(self, action: PurgeVFolderAction) -> PurgeVFolderActionResult:
        pass

    async def clone(self, action: CloneVFolderAction) -> CloneVFolderActionResult:
        pass

    # Invite operations
    async def invite(self, action: InviteVFolderAction) -> InviteVFolderActionResult:
        pass

    async def receive_invitation(
        self, action: ReceiveInvitationAction
    ) -> ReceiveInvitationActionResult:
        pass

    async def update_invitation(
        self, action: UpdateInvitationAction
    ) -> UpdateInvitationActionResult:
        pass

    async def list_invitation(self, action: ListInvitationAction) -> ListInvitationActionResult:
        pass

    async def leave_invited_vfolder(
        self, action: LeaveInvitedVFolderAction
    ) -> LeaveInvitedVFolderActionResult:
        pass

    # File operations
    async def upload_file(self, action: UploadFileAction) -> UploadFileActionResult:
        pass

    async def download_file(self, action: DownloadFileAction) -> DownloadFileActionResult:
        pass

    async def list_files(self, action: ListFilesAction) -> ListFilesActionResult:
        pass

    async def rename_file(self, action: RenameFileAction) -> RenameFileActionResult:
        pass

    async def delete_files(self, action: DeleteFilesAction) -> DeleteFilesActionResult:
        pass

    async def mkdir(self, action: MkdirAction) -> MkdirActionResult:
        pass
