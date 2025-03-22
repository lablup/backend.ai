from dataclasses import dataclass

from ....models.utils import ExtendedAsyncSAEngine
from ....registry import AgentRegistry
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


@dataclass
class ServiceInitParameter:
    db: ExtendedAsyncSAEngine
    registry: AgentRegistry


class VFolderFileService:
    _db: ExtendedAsyncSAEngine
    _registry: AgentRegistry

    def __init__(self, parameter: ServiceInitParameter) -> None:
        self._db = parameter.db
        self._registry = parameter.registry

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
