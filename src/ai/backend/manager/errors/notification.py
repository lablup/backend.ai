"""Notification-related error definitions."""

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.notification import (
    NotificationChannelEntityType,
    NotificationRuleEntityType,
)
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode

__all__ = (
    "InvalidNotificationChannelType",
    "InvalidNotificationSpec",
    "NotificationChannelNotFound",
    "NotificationProcessingFailure",
    "NotificationRuleNotFound",
    "NotificationTemplateRenderingFailure",
)


class NotificationChannelNotFound(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/notification-channel-not-found"
    error_title = "The notification channel does not exist."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            NotificationChannelEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class NotificationRuleNotFound(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/notification-rule-not-found"
    error_title = "The notification rule does not exist."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            NotificationRuleEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class NotificationProcessingFailure(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/notification-processing-failure"
    error_title = "Failed to process notification."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.NOTIFICATION,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NotificationTemplateRenderingFailure(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/notification-template-rendering-failure"
    error_title = "Failed to render notification template."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            NotificationRuleEntityType(),
            ActionOperationType.GET,
            ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidNotificationChannelType(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-notification-channel-type"
    error_title = "Invalid notification channel type."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            NotificationChannelEntityType(),
            ActionOperationType.CREATE,
            ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidNotificationSpec(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-notification-spec"
    error_title = "Invalid notification specification."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            NotificationChannelEntityType(),
            ActionOperationType.GET,
            ErrorDetail.INVALID_PARAMETERS,
        )
