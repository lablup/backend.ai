from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ArtifactRegistryNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-registry-not-found"
    error_title = "Artifact Registry Not Found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ArtifactRegistryBadScanRequestError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/artifact-registry-bad-scan-request"
    error_title = "Artifact Registry Bad Scan Request"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
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
