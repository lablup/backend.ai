"""
Image and container registry-related exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.image_alias import ImageAliasFieldType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode

from .common import InternalServerError, ObjectNotFound


class ImageNotFound(EntityError, ObjectNotFound):
    object_name = "environment image"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(ImageEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class ImagePurgeInProgress(EntityError, web.HTTPConflict):
    """Raised when a write names an image a purge is working through."""

    error_type = "https://api.backend.ai/probs/image-purge-in-progress"
    error_title = "Image is being purged."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(ImageEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT)


class ImageAliasNotFound(FieldError, ObjectNotFound):
    object_name = "image alias"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(ImageAliasFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class ContainerRegistryNotFound(EntityError, ObjectNotFound):
    object_name = "container_registry"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ContainerRegistryGroupsAssociationNotFound(ObjectNotFound):
    object_name = "association of container_registry and group"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ContainerRegistryWebhookAuthorizationFailed(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/webhook/auth-failed"
    error_title = "Container Registry Webhook authorization failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.HOOK,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class HarborWebhookContainerRegistryRowNotFound(EntityError, InternalServerError):
    error_type = "https://api.backend.ai/probs/webhook/harbor/container-registry-not-found"
    error_title = "Container registry row not found."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class UnknownImageReferenceError(EntityError, ObjectNotFound):
    object_name = "image reference"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ImageEntityType(), ActionOperationType.GET, ErrorDetail.INTERNAL_ERROR
        )


class ImageAccessForbiddenError(BackendAIError):
    """Raised when a user tries to access an image they do not have permission to access."""

    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "User does not have permission to access this image."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class AliasImageActionValueError(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-parameters"
    error_title = "Invalid parameters for image alias."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            ImageAliasFieldType(), ActionOperationType.CREATE, ErrorDetail.INVALID_PARAMETERS
        )


class AliasImageActionDBError(FieldError, web.HTTPInternalServerError):
    """
    This can occur when an image alias with the same value already exists.
    """

    error_type = "https://api.backend.ai/probs/image-db-error"
    error_title = "Database error while managing image alias."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            ImageAliasFieldType(), ActionOperationType.UPDATE, ErrorDetail.ALREADY_EXISTS
        )


class UpdateImageActionValueError(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-parameters"
    error_title = "Invalid parameters for image modification."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ImageEntityType(), ActionOperationType.UPDATE, ErrorDetail.INVALID_PARAMETERS
        )


class PurgeImageActionByIdObjectDBError(EntityError, web.HTTPInternalServerError):
    """
    This can occur when the alias of the image you are trying to delete already exists.
    """

    error_type = "https://api.backend.ai/probs/image-db-error"
    error_title = "Database error while purging image."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ImageEntityType(), ActionOperationType.PURGE, ErrorDetail.INTERNAL_ERROR
        )


class RegistryNotFoundForImage(EntityError, ObjectNotFound):
    object_name = "registry for image"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ContainerRegistryEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )
