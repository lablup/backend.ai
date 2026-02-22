from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

if TYPE_CHECKING:
    from ai.backend.common.types import QuotaScopeID, VFolderID


class VFolderQuotaExceededError(BackendAIError, web.HTTPBadRequest):
    """
    Raised when a VFolder quota scope limit would be exceeded by an operation.

    This error is raised during pre-validation before operations like artifact import,
    preventing partial downloads and wasted resources.
    """

    error_type = "https://api.backend.ai/probs/vfolder-quota-exceeded"
    error_title = "VFolder Quota Scope Limit Would Be Exceeded"

    def __init__(
        self,
        vfolder_id: VFolderID,
        quota_scope_id: QuotaScopeID,
        current_size: int,
        max_size: int,
        requested_size: int,
    ) -> None:
        self.vfolder_id = vfolder_id
        self.quota_scope_id = quota_scope_id
        self.current_size = current_size
        self.max_size = max_size
        self.requested_size = requested_size
        available_bytes = max_size - current_size

        message = (
            f"VFolder quota scope limit would be exceeded. "
            f"Current: {current_size} bytes, Max: {max_size} bytes, "
            f"Requested: {requested_size} bytes, Available: {available_bytes} bytes"
        )
        super().__init__(message)

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.BAD_REQUEST,
        )

    def error_data(self) -> dict[str, Any]:
        return {
            "vfolder_id": str(self.vfolder_id),
            "quota_scope_id": str(self.quota_scope_id),
            "current_size_bytes": self.current_size,
            "max_size_bytes": self.max_size,
            "requested_size_bytes": self.requested_size,
            "available_bytes": self.max_size - self.current_size,
        }
