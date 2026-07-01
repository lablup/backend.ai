from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.vfolder.actions.file import (
    CreateArchiveDownloadSessionAction,
    CreateArchiveDownloadSessionActionResult,
    CreateDownloadSessionAction,
    CreateDownloadSessionActionResult,
    CreateUploadSessionAction,
    CreateUploadSessionActionResult,
    DeleteFilesAction,
    DeleteFilesActionResult,
    DeleteFilesAsyncAction,
    DeleteFilesAsyncActionResult,
    ListFilesAction,
    ListFilesActionResult,
    MkdirAction,
    MkdirActionResult,
    MoveFileAction,
    MoveFileActionResult,
    RenameFileAction,
    RenameFileActionResult,
)
from ai.backend.manager.services.vfolder.actions.file_v2 import (
    CreateDownloadSessionV2Action,
    CreateDownloadSessionV2ActionResult,
    DeleteFilesV2Action,
    DeleteFilesV2ActionResult,
    ListFilesV2Action,
    ListFilesV2ActionResult,
    MkdirV2Action,
    MkdirV2ActionResult,
    MoveFileV2Action,
    MoveFileV2ActionResult,
)
from ai.backend.manager.services.vfolder.services.file import VFolderFileService


class VFolderFileProcessors(AbstractProcessorPackage):
    upload_file: ActionProcessor[CreateUploadSessionAction, CreateUploadSessionActionResult]
    download_file: ActionProcessor[CreateDownloadSessionAction, CreateDownloadSessionActionResult]
    create_archive_download_session: ActionProcessor[
        CreateArchiveDownloadSessionAction, CreateArchiveDownloadSessionActionResult
    ]
    list_files: ActionProcessor[ListFilesAction, ListFilesActionResult]
    rename_file: ActionProcessor[RenameFileAction, RenameFileActionResult]
    delete_files: ActionProcessor[DeleteFilesAction, DeleteFilesActionResult]
    delete_files_async: ActionProcessor[DeleteFilesAsyncAction, DeleteFilesAsyncActionResult]
    mkdir: ActionProcessor[MkdirAction, MkdirActionResult]
    move_file: ActionProcessor[MoveFileAction, MoveFileActionResult]
    # V2 processors
    list_files_v2: ActionProcessor[ListFilesV2Action, ListFilesV2ActionResult]
    mkdir_v2: ActionProcessor[MkdirV2Action, MkdirV2ActionResult]
    move_file_v2: ActionProcessor[MoveFileV2Action, MoveFileV2ActionResult]
    delete_files_v2: ActionProcessor[DeleteFilesV2Action, DeleteFilesV2ActionResult]
    download_file_v2: ActionProcessor[
        CreateDownloadSessionV2Action, CreateDownloadSessionV2ActionResult
    ]

    def __init__(
        self,
        service: VFolderFileService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.upload_file = ActionProcessor(service.upload_file, action_monitors)
        self.download_file = ActionProcessor(service.download_file, action_monitors)
        self.create_archive_download_session = ActionProcessor(
            service.create_archive_download_session, action_monitors
        )
        self.list_files = ActionProcessor(service.list_files, action_monitors)
        self.rename_file = ActionProcessor(service.rename_file, action_monitors)
        self.delete_files = ActionProcessor(service.delete_files, action_monitors)
        self.delete_files_async = ActionProcessor(service.delete_files_async, action_monitors)
        self.mkdir = ActionProcessor(service.mkdir, action_monitors)
        self.move_file = ActionProcessor(service.move_file, action_monitors)
        # V2
        self.list_files_v2 = ActionProcessor(service.list_files_v2, action_monitors)
        self.mkdir_v2 = ActionProcessor(service.mkdir_v2, action_monitors)
        self.move_file_v2 = ActionProcessor(service.move_file_v2, action_monitors)
        self.delete_files_v2 = ActionProcessor(service.delete_files_v2, action_monitors)
        self.download_file_v2 = ActionProcessor(service.download_file_v2, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateUploadSessionAction.spec(),
            CreateDownloadSessionAction.spec(),
            CreateArchiveDownloadSessionAction.spec(),
            ListFilesAction.spec(),
            RenameFileAction.spec(),
            DeleteFilesAction.spec(),
            DeleteFilesAsyncAction.spec(),
            MkdirAction.spec(),
            MoveFileAction.spec(),
            ListFilesV2Action.spec(),
            MkdirV2Action.spec(),
            MoveFileV2Action.spec(),
            DeleteFilesV2Action.spec(),
            CreateDownloadSessionV2Action.spec(),
        ]
