from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class PrometheusConnectionError(BackendAIError, web.HTTPServiceUnavailable):
    """Exception raised when a connection to Prometheus fails."""

    error_type = "https://api.backend.ai/probs/prometheus-connection-error"
    error_title = "Failed to connect to Prometheus."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.METRIC,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class PrometheusQueryEvaluationFailed(BackendAIError, web.HTTPBadRequest):
    """Raised when Prometheus rejects a rendered PromQL query.

    Used by user-facing flows (e.g., preset preview) to attribute query
    rejection to the caller's input rather than treating it as a downstream
    gateway failure (502).
    """

    error_type = "https://api.backend.ai/probs/prometheus-query-evaluation-failed"
    error_title = "Prometheus rejected the query."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.METRIC,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class PrometheusQueryPresetNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/prometheus-query-preset-not-found"
    error_title = "The prometheus query preset does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PROMETHEUS_QUERY_PRESET,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class PrometheusQueryPresetInvalidLabel(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/prometheus-query-preset-invalid-label"
    error_title = "Invalid label specified for prometheus query preset execution."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PROMETHEUS_QUERY_PRESET,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class PrometheusQueryPresetCategoryNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/prometheus-query-preset-category-not-found"
    error_title = "The prometheus query preset category does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PROMETHEUS_QUERY_PRESET_CATEGORY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
