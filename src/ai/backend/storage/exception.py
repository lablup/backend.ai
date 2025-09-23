from pathlib import PurePosixPath

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import VFolderID


class StorageProxyError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/generic"
    error_title = "Storage Proxy Error"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ProcessExecutionError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/execution/failed"
    error_title = "Storage Operation Execution Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ExternalStorageServiceError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/external/failed"
    error_title = "External Operation Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NetAppClientError(ExternalStorageServiceError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/storage/netapp/api-error"
    error_title = "NetApp API Error"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage/vfolder/not-found"
    error_title = "VFolder Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class QuotaDirectoryNotEmptyError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/storage/quota-directory-not-empty"
    error_title = "Quota Directory Not Empty"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class QuotaScopeNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage/quota/scope/not-found"
    error_title = "Quota Scope Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class QuotaScopeAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/storage/quota/scope/already-exists"
    error_title = "Quota Scope Already Exists"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class InvalidQuotaConfig(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/quota/config/invalid"
    error_title = "Invalid Quota Config"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidSubpathError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/subpath/invalid"
    error_title = "Invalid Subpath"

    def __init__(self, vfid: VFolderID, relpath: PurePosixPath) -> None:
        msg_str = f"Invalid Subpath (vfid={vfid}, relpath={relpath})"
        super().__init__(extra_msg=msg_str, extra_data=msg_str)

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidQuotaScopeError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/quota/scope/invalid"
    error_title = "Invalid Quota Scope"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidVolumeError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/volume/invalid"
    error_title = "Invalid Volume"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidAPIParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/invalid-api-params"
    error_title = "Invalid API parameters"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class FileStreamUploadError(ProcessExecutionError):
    error_type = "https://api.backend.ai/probs/storage/file-stream-upload-failed"
    error_title = "Failed to upload file stream"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class FileStreamDownloadError(ProcessExecutionError):
    error_type = "https://api.backend.ai/probs/storage/file-stream-download-failed"
    error_title = "Failed to download file stream"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class PresignedUploadURLGenerationError(ProcessExecutionError):
    error_type = "https://api.backend.ai/probs/storage/presigned-upload-url-generation-failed"
    error_title = "Failed to generate presigned upload URL"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class PresignedDownloadURLGenerationError(ProcessExecutionError):
    error_type = "https://api.backend.ai/probs/storage/presigned-download-url-generation-failed"
    error_title = "Failed to generate presigned download URL"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ObjectInfoFetchError(ProcessExecutionError):
    error_type = "https://api.backend.ai/probs/storage/object-info-fetch-failed"
    error_title = "Failed to fetch object info"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class StorageNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage/object-not-found"
    error_title = "Storage Config Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class StorageTypeInvalidError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/object-type-invalid"
    error_title = "Storage Config Invalid Type"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ObjectStorageBucketNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage/bucket/object-not-found"
    error_title = "Storage Bucket Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class StorageBucketFileNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage/bucket/file/object-not-found"
    error_title = "Storage Bucket File Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RegistryNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/registries/registry-not-found"
    error_title = "Registry Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class HuggingFaceAPIError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/registries/huggingface/api-error"
    error_title = "HuggingFace API Error"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT_REGISTRY,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class HuggingFaceModelNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/registries/huggingface/model-not-found"
    error_title = "HuggingFace Model Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ObjectStorageConfigInvalidError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/object/config/invalid"
    error_title = "Object Storage Config Invalid"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ReservoirStorageConfigInvalidError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/reservoir/config/invalid"
    error_title = "Reservoir Storage Config Invalid"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ArtifactStorageEmptyError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage/artifact/config/invalid"
    error_title = "Artifact Storage Empty"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ArtifactRevisionEmptyError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/artifact/revision/empty"
    error_title = "Artifact Revision Empty"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ArtifactImportError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/artifact/import/failed"
    error_title = "Artifact Import Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NotImplementedAPI(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/api/not-implemented"
    error_title = "API Not Implemented"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class ObjectStorageObjectDeletionError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/storage/object/deletion/failed"
    error_title = "Object Deletion Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.OBJECT_STORAGE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
