"""Exceptions for validators."""

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class SchedulingValidationError(BackendAIError, web.HTTPPreconditionFailed):
    """Base exception for validation errors in the Sokovan scheduler."""

    error_type = "https://api.backend.ai/probs/scheduling-validation-failed"
    error_title = "Scheduling validation failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ConcurrencyLimitExceeded(SchedulingValidationError):
    """Raised when concurrent session limit is exceeded."""

    error_type = "https://api.backend.ai/probs/concurrency-limit-exceeded"
    error_title = "Concurrent session limit exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class DependenciesNotSatisfied(SchedulingValidationError):
    """Raised when session dependencies are not satisfied."""

    error_type = "https://api.backend.ai/probs/dependencies-not-satisfied"
    error_title = "Session dependencies not satisfied."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.NOT_READY,
        )


class KeypairResourceQuotaExceeded(SchedulingValidationError):
    """Raised when keypair resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/keypair-resource-quota-exceeded"
    error_title = "Keypair resource quota exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class UserResourceQuotaExceeded(SchedulingValidationError):
    """Raised when user resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/user-resource-quota-exceeded"
    error_title = "User resource quota exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class GroupResourceQuotaExceeded(SchedulingValidationError):
    """Raised when group resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/group-resource-quota-exceeded"
    error_title = "Group resource quota exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class DomainResourceQuotaExceeded(SchedulingValidationError):
    """Raised when domain resource quota is exceeded."""

    error_type = "https://api.backend.ai/probs/domain-resource-quota-exceeded"
    error_title = "Domain resource quota exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class PendingSessionCountLimitExceeded(SchedulingValidationError):
    """Raised when pending session count limit is exceeded."""

    error_type = "https://api.backend.ai/probs/pending-session-count-limit-exceeded"
    error_title = "Pending session count limit exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class PendingSessionResourceLimitExceeded(SchedulingValidationError):
    """Raised when pending session resource limit is exceeded."""

    error_type = "https://api.backend.ai/probs/pending-session-resource-limit-exceeded"
    error_title = "Pending session resource limit exceeded."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class UserResourcePolicyNotFound(SchedulingValidationError):
    """Raised when user has no resource policy."""

    error_type = "https://api.backend.ai/probs/user-resource-policy-not-found"
    error_title = "User resource policy not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
