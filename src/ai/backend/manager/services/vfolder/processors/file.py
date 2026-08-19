from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.vfolder.types import VFolderData
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


class VFolderFileProcessors:
    upload_file: SingleEntityActionProcessor[
        CreateUploadSessionAction, CreateUploadSessionActionResult
    ]
    download_file: SingleEntityActionProcessor[
        CreateDownloadSessionAction, CreateDownloadSessionActionResult
    ]
    create_archive_download_session: SingleEntityActionProcessor[
        CreateArchiveDownloadSessionAction, CreateArchiveDownloadSessionActionResult
    ]
    list_files: SingleEntityActionProcessor[ListFilesAction, ListFilesActionResult]
    rename_file: SingleEntityActionProcessor[RenameFileAction, RenameFileActionResult]
    delete_files: SingleEntityActionProcessor[DeleteFilesAction, DeleteFilesActionResult]
    delete_files_async: SingleEntityActionProcessor[
        DeleteFilesAsyncAction, DeleteFilesAsyncActionResult
    ]
    mkdir: SingleEntityActionProcessor[MkdirAction, MkdirActionResult]
    move_file: SingleEntityActionProcessor[MoveFileAction, MoveFileActionResult]
    # V2 processors
    list_files_v2: SingleEntityActionProcessor[ListFilesV2Action, ListFilesV2ActionResult]
    mkdir_v2: SingleEntityActionProcessor[MkdirV2Action, MkdirV2ActionResult]
    move_file_v2: SingleEntityActionProcessor[MoveFileV2Action, MoveFileV2ActionResult]
    delete_files_v2: SingleEntityActionProcessor[DeleteFilesV2Action, DeleteFilesV2ActionResult]
    download_file_v2: SingleEntityActionProcessor[
        CreateDownloadSessionV2Action, CreateDownloadSessionV2ActionResult
    ]

    def __init__(self, group: ProcessorGroup[VFolderData], service: VFolderFileService) -> None:
        self.upload_file = group.single_entity(CreateUploadSessionAction, service.upload_file)
        self.download_file = group.single_entity(CreateDownloadSessionAction, service.download_file)
        self.create_archive_download_session = group.single_entity(
            CreateArchiveDownloadSessionAction, service.create_archive_download_session
        )
        self.list_files = group.single_entity(ListFilesAction, service.list_files)
        self.rename_file = group.single_entity(RenameFileAction, service.rename_file)
        self.delete_files = group.single_entity(DeleteFilesAction, service.delete_files)
        self.delete_files_async = group.single_entity(
            DeleteFilesAsyncAction, service.delete_files_async
        )
        self.mkdir = group.single_entity(MkdirAction, service.mkdir)
        self.move_file = group.single_entity(MoveFileAction, service.move_file)
        # V2
        self.list_files_v2 = group.single_entity(ListFilesV2Action, service.list_files_v2)
        self.mkdir_v2 = group.single_entity(MkdirV2Action, service.mkdir_v2)
        self.move_file_v2 = group.single_entity(MoveFileV2Action, service.move_file_v2)
        self.delete_files_v2 = group.single_entity(DeleteFilesV2Action, service.delete_files_v2)
        self.download_file_v2 = group.single_entity(
            CreateDownloadSessionV2Action, service.download_file_v2
        )
