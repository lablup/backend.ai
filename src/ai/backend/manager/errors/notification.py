"""Notification-related error definitions."""

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = (
    "NotificationChannelNotFound",
    "NotificationRuleNotFound",
    "NotificationChannelConflict",
    "NotificationRuleConflict",
    "NotificationProcessingFailure",
    "NotificationTemplateRenderingFailure",
    "InvalidNotificationChannelType",
    "InvalidNotificationConfig",
)


class NotificationChannelNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/notification-channel-not-found"
    error_title = "The notification channel does not exist."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class NotificationRuleNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/notification-rule-not-found"
    error_title = "The notification rule does not exist."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class NotificationChannelConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/notification-channel-conflict"
    error_title = "The notification channel already exists."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class NotificationRuleConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/notification-rule-conflict"
    error_title = "The notification rule already exists."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class NotificationProcessingFailure(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/notification-processing-failure"
    error_title = "Failed to process notification."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NotificationTemplateRenderingFailure(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/notification-template-rendering-failure"
    error_title = "Failed to render notification template."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidNotificationChannelType(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-notification-channel-type"
    error_title = "Invalid notification channel type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidNotificationConfig(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-notification-config"
    error_title = "Invalid notification configuration."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
