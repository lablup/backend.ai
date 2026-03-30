from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class VFSStorageNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/vfs-storage-not-found"
    error_title = "VFS Storage Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFS_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
