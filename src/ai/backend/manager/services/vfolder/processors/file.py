from ai.backend.manager.actions.processor import ActionProcessor

from ..actions.file import (
    DeleteFilesAction,
    DeleteFilesActionResult,
    DownloadFileAction,
    DownloadFileActionResult,
    ListFilesAction,
    ListFilesActionResult,
    MkdirAction,
    MkdirActionResult,
    RenameFileAction,
    RenameFileActionResult,
    UploadFileAction,
    UploadFileActionResult,
)
from ..services.file import VFolderFileService


class VFolderFileProcessors:
    upload_file = ActionProcessor[UploadFileAction, UploadFileActionResult]
    download_file = ActionProcessor[DownloadFileAction, DownloadFileActionResult]
    list_files = ActionProcessor[ListFilesAction, ListFilesActionResult]
    rename_file = ActionProcessor[RenameFileAction, RenameFileActionResult]
    delete_files = ActionProcessor[DeleteFilesAction, DeleteFilesActionResult]
    mkdir = ActionProcessor[MkdirAction, MkdirActionResult]

    def __init__(self, service: VFolderFileService) -> None:
        self.upload_file = ActionProcessor(service.upload_file)
        self.download_file = ActionProcessor(service.download_file)
        self.list_files = ActionProcessor(service.list_files)
        self.rename_file = ActionProcessor(service.rename_file)
        self.delete_files = ActionProcessor(service.delete_files)
        self.mkdir = ActionProcessor(service.mkdir)
