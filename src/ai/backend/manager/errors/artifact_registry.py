from typing import override

from aiohttp import web

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryEntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class ArtifactRegistryNotFoundError(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-registry-not-found"
    error_title = "Artifact Registry Not Found"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ArtifactRegistryEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ArtifactRegistryBadScanRequestError(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-registry-bad-scan-request"
    error_title = "Artifact Registry Bad Scan Request"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ArtifactRegistryEntityType(), ActionOperationType.GET, ErrorDetail.BAD_REQUEST
        )


class InvalidArtifactRegistryTypeError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/invalid-artifact-registry-type"
    error_title = "Invalid Artifact Registry Type"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class ReservoirConnectionError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/reservoir-connection-error"
    error_title = "Reservoir Connection Error"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class RemoteReservoirScanError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/remote-reservoir-scan-error"
    error_title = "Remote Reservoir Scan Error"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
