from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from ..actions.file import (
    CreateDownloadSessionAction,
    CreateDownloadSessionActionResult,
    CreateUploadSessionAction,
    CreateUploadSessionActionResult,
    DeleteFilesAction,
    DeleteFilesActionResult,
    ListFilesAction,
    ListFilesActionResult,
    MkdirAction,
    MkdirActionResult,
    RenameFileAction,
    RenameFileActionResult,
)
from ..services.file import VFolderFileService


class VFolderFileProcessors(AbstractProcessorPackage):
    upload_file: ActionProcessor[CreateUploadSessionAction, CreateUploadSessionActionResult]
    download_file: ActionProcessor[CreateDownloadSessionAction, CreateDownloadSessionActionResult]
    list_files: ActionProcessor[ListFilesAction, ListFilesActionResult]
    rename_file: ActionProcessor[RenameFileAction, RenameFileActionResult]
    delete_files: ActionProcessor[DeleteFilesAction, DeleteFilesActionResult]
    mkdir: ActionProcessor[MkdirAction, MkdirActionResult]

    def __init__(self, service: VFolderFileService, action_monitors: list[ActionMonitor]) -> None:
        self.upload_file = ActionProcessor(service.upload_file, action_monitors)
        self.download_file = ActionProcessor(service.download_file, action_monitors)
        self.list_files = ActionProcessor(service.list_files, action_monitors)
        self.rename_file = ActionProcessor(service.rename_file, action_monitors)
        self.delete_files = ActionProcessor(service.delete_files, action_monitors)
        self.mkdir = ActionProcessor(service.mkdir, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateUploadSessionAction.spec(),
            CreateDownloadSessionAction.spec(),
            ListFilesAction.spec(),
            RenameFileAction.spec(),
            DeleteFilesAction.spec(),
            MkdirAction.spec(),
        ]
