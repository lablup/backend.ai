from ai.backend.manager.actions.action import BaseActionResult

from .base import VFolderAction


class UploadFileAction(VFolderAction):
    pass


class UploadFileActionResult(BaseActionResult):
    pass


class DownloadFileAction(VFolderAction):
    pass


class DownloadFileActionResult(BaseActionResult):
    pass


class ListFilesAction(VFolderAction):
    pass


class ListFilesActionResult(BaseActionResult):
    pass


class RenameFileAction(VFolderAction):
    pass


class RenameFileActionResult(BaseActionResult):
    pass


class DeleteFilesAction(VFolderAction):
    pass


class DeleteFilesActionResult(BaseActionResult):
    pass


class MkdirAction(VFolderAction):
    pass


class MkdirActionResult(BaseActionResult):
    pass
