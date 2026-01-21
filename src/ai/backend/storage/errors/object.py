"""
Object storage and artifact-related exceptions.
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

from .base import ProcessExecutionError


class FileStreamUploadError(ProcessExecutionError):
    """Raised when file stream upload fails."""

    error_type = "https://api.backend.ai/probs/storage/file-stream-upload-failed"
    error_title = "Failed to upload file stream"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class FileStreamDownloadError(ProcessExecutionError):
    """Raised when file stream download fails."""

    error_type = "https://api.backend.ai/probs/storage/file-stream-download-failed"
    error_title = "Failed to download file stream"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class PresignedUploadURLGenerationError(ProcessExecutionError):
    """Raised when presigned upload URL generation fails."""

    error_type = "https://api.backend.ai/probs/storage/presigned-upload-url-generation-failed"
    error_title = "Failed to generate presigned upload URL"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class PresignedDownloadURLGenerationError(ProcessExecutionError):
    """Raised when presigned download URL generation fails."""

    error_type = "https://api.backend.ai/probs/storage/presigned-download-url-generation-failed"
    error_title = "Failed to generate presigned download URL"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ObjectInfoFetchError(ProcessExecutionError):
    """Raised when object info fetch fails."""

    error_type = "https://api.backend.ai/probs/storage/object-info-fetch-failed"
    error_title = "Failed to fetch object info"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ObjectStorageBucketNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when an object storage bucket is not found."""

    error_type = "https://api.backend.ai/probs/storage/bucket/object-not-found"
    error_title = "Storage Bucket Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class StorageBucketFileNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a file in storage bucket is not found."""

    error_type = "https://api.backend.ai/probs/storage/bucket/file/object-not-found"
    error_title = "Storage Bucket File Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ObjectStorageConfigInvalidError(BackendAIError, web.HTTPBadRequest):
    """Raised when object storage config is invalid."""

    error_type = "https://api.backend.ai/probs/storage/object/config/invalid"
    error_title = "Object Storage Config Invalid"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ReservoirStorageConfigInvalidError(BackendAIError, web.HTTPBadRequest):
    """Raised when reservoir storage config is invalid."""

    error_type = "https://api.backend.ai/probs/storage/reservoir/config/invalid"
    error_title = "Reservoir Storage Config Invalid"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFS_STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ObjectStorageObjectDeletionError(BackendAIError, web.HTTPBadRequest):
    """Raised when object deletion fails."""

    error_type = "https://api.backend.ai/probs/storage/object/deletion/failed"
    error_title = "Object Deletion Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


# Registry and artifact exceptions


class RegistryNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a registry is not found."""

    error_type = "https://api.backend.ai/probs/registries/registry-not-found"
    error_title = "Registry Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class HuggingFaceAPIError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a HuggingFace API call fails."""

    error_type = "https://api.backend.ai/probs/registries/huggingface/api-error"
    error_title = "HuggingFace API Error"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class HuggingFaceModelNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a HuggingFace model is not found."""

    error_type = "https://api.backend.ai/probs/registries/huggingface/model-not-found"
    error_title = "HuggingFace Model Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ArtifactStorageEmptyError(BackendAIError, web.HTTPNotFound):
    """Raised when artifact storage is empty."""

    error_type = "https://api.backend.ai/probs/storage/artifact/config/invalid"
    error_title = "Artifact Storage Empty"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ArtifactRevisionEmptyError(BackendAIError, web.HTTPBadRequest):
    """Raised when artifact revision is empty."""

    error_type = "https://api.backend.ai/probs/storage/artifact/revision/empty"
    error_title = "Artifact Revision Empty"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ArtifactImportError(BackendAIError, web.HTTPInternalServerError):
    """Raised when artifact import fails."""

    error_type = "https://api.backend.ai/probs/storage/artifact/import/failed"
    error_title = "Artifact Import Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ArtifactVerifyStorageTypeInvalid(BackendAIError, web.HTTPBadRequest):
    """Raised when artifact verification storage type is invalid."""

    error_type = "https://api.backend.ai/probs/storage/artifact/verify/storage-type/invalid"
    error_title = "Artifact Verify Storage Type Invalid"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ArtifactVerificationFailedError(BackendAIError, web.HTTPBadRequest):
    """Raised when artifact verification fails."""

    error_type = "https://api.backend.ai/probs/storage/artifact/verification/failed"
    error_title = "Artifact Verification Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.MISMATCH,
        )
