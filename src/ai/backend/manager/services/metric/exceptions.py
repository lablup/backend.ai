from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class FailedToGetMetric(BackendAIError):
    """Exception raised when a metric cannot be retrieved."""

    error_type = "https://api.backend.ai/probs/failed-to-get-metric"
    error_title = "Failed to get metric."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.METRIC,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
