"""
Process/subprocess execution exceptions.
"""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

from .base import ExternalStorageServiceError


class SubprocessStdoutNotAvailableError(BackendAIError, web.HTTPInternalServerError):
    """Raised when subprocess stdout is not available."""

    error_type = "https://api.backend.ai/probs/storage/subprocess/stdout-unavailable"
    error_title = "Subprocess Stdout Not Available"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class QuotaCommandFailedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a quota command fails."""

    error_type = "https://api.backend.ai/probs/storage/quota/command-failed"
    error_title = "Quota Command Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class CephNotInstalledError(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when Ceph is not installed."""

    error_type = "https://api.backend.ai/probs/storage/ceph/not-installed"
    error_title = "Ceph Not Installed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class PureStorageCommandFailedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a PureStorage command fails."""

    error_type = "https://api.backend.ai/probs/storage/purestorage/command-failed"
    error_title = "PureStorage Command Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NetAppClientError(ExternalStorageServiceError, web.HTTPServiceUnavailable):
    """Raised when a NetApp API call fails."""

    error_type = "https://api.backend.ai/probs/storage/netapp/api-error"
    error_title = "NetApp API Error"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class NetAppQTreeNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a NetApp qtree is not found."""

    error_type = "https://api.backend.ai/probs/storage/netapp/qtree-not-found"
    error_title = "NetApp QTree Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DDNCommandFailedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a DDN lfs command fails."""

    error_type = "https://api.backend.ai/probs/storage/ddn/command-failed"
    error_title = "DDN Command Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class MetricNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a metric is not found."""

    error_type = "https://api.backend.ai/probs/storage/metric-not-found"
    error_title = "Metric Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
