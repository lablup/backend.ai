"""
VFolder-related exceptions.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import VFolderID


class VFolderNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a VFolder is not found."""

    error_type = "https://api.backend.ai/probs/storage/vfolder/not-found"
    error_title = "VFolder Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidSubpathError(BackendAIError, web.HTTPBadRequest):
    """Raised when a subpath is invalid."""

    error_type = "https://api.backend.ai/probs/storage/subpath/invalid"
    error_title = "Invalid Subpath"

    def __init__(self, vfid: VFolderID, relpath: PurePosixPath) -> None:
        msg_str = f"Invalid Subpath (vfid={vfid}, relpath={relpath})"
        super().__init__(extra_msg=msg_str, extra_data=msg_str)

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
