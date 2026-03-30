from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class GPFSError(BackendAIError):
    """Base error for GPFS-related errors."""


class GPFSInitError(GPFSError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/gpfs-init-error"
    error_title = "GPFS initialization failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.SETUP, ErrorDetail.NOT_READY)


class GPFSAPIError(GPFSError):
    error_type = "https://api.backend.ai/probs/gpfs-api-error"
    error_title = "GPFS API error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.REQUEST, ErrorDetail.INTERNAL_ERROR)


class GPFSInvalidBodyError(GPFSAPIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/gpfs-bad-request"
    error_title = "GPFS API bad request."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.REQUEST, ErrorDetail.BAD_REQUEST)


class GPFSUnauthorizedError(GPFSAPIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/gpfs-authentication-failure"
    error_title = "GPFS API authentication failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.AUTH, ErrorDetail.UNAUTHORIZED)


class GPFSForbiddenError(GPFSAPIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/gpfs-forbidden"
    error_title = "GPFS API access forbidden."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.AUTH, ErrorDetail.FORBIDDEN)


class GPFSNotFoundError(GPFSAPIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/gpfs-not-found"
    error_title = "GPFS resource not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.READ, ErrorDetail.NOT_FOUND)


class GPFSConflictError(GPFSAPIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/gpfs-conflict"
    error_title = "GPFS resource conflict."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.CREATE, ErrorDetail.CONFLICT)


class GPFSInternalError(GPFSAPIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/gpfs-internal-error"
    error_title = "GPFS internal error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.REQUEST, ErrorDetail.INTERNAL_ERROR)


class GPFSNoMetricError(GPFSError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/gpfs-no-metric"
    error_title = "GPFS metric not available."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.READ, ErrorDetail.NOT_FOUND)


class GPFSJobFailedError(GPFSError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/gpfs-job-failed"
    error_title = "GPFS job failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.EXECUTE, ErrorDetail.INTERNAL_ERROR)


class GPFSJobCancelledError(GPFSError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/gpfs-job-cancelled"
    error_title = "GPFS job was cancelled."

    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.EXECUTE, ErrorDetail.CANCELED)
