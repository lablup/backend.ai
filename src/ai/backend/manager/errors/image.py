"""
Image and container registry-related exceptions.
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

from .common import InternalServerError, ObjectNotFound


class ImageNotFound(ObjectNotFound):
    object_name = "environment image"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ImageAliasNotFound(ObjectNotFound):
    object_name = "image alias"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE_ALIAS,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ContainerRegistryNotFound(ObjectNotFound):
    object_name = "container_registry"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ContainerRegistryGroupsAssociationNotFound(ObjectNotFound):
    object_name = "association of container_registry and group"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ContainerRegistryWebhookAuthorizationFailed(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/webhook/auth-failed"
    error_title = "Container Registry Webhook authorization failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.HOOK,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class HarborWebhookContainerRegistryRowNotFound(InternalServerError):
    error_type = "https://api.backend.ai/probs/webhook/harbor/container-registry-not-found"
    error_title = "Container registry row not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class UnknownImageReferenceError(ObjectNotFound):
    object_name = "image reference"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ForgetImageForbiddenError(BackendAIError):
    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "Access to this resource is forbidden."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class ForgetImageNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/generic-not-found"
    error_title = "The image you are trying to delete does not exist."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AliasImageActionValueError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-parameters"
    error_title = "Invalid parameters for image alias."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE_ALIAS,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AliasImageActionDBError(BackendAIError, web.HTTPInternalServerError):
    """
    This can occur when an image alias with the same value already exists.
    """

    error_type = "https://api.backend.ai/probs/image-db-error"
    error_title = "Database error while managing image alias."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE_ALIAS,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class ModifyImageActionValueError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-parameters"
    error_title = "Invalid parameters for image modification."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class PurgeImageActionByIdObjectDBError(BackendAIError, web.HTTPInternalServerError):
    """
    This can occur when the alias of the image you are trying to delete already exists.
    """

    error_type = "https://api.backend.ai/probs/image-db-error"
    error_title = "Database error while purging image."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class RegistryNotFoundForImage(ObjectNotFound):
    object_name = "registry for image"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
