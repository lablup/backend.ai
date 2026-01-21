"""
Storage proxy error classes.
"""

from .base import (
    ExternalStorageServiceError,
    NotImplementedAPI,
    ProcessExecutionError,
    StorageProxyError,
)
from .common import (
    InvalidAPIParameters,
    InvalidConfigurationSourceError,
    InvalidDataLengthError,
    InvalidPathError,
    InvalidSocketPathError,
    ServiceNotInitializedError,
    StorageNotFoundError,
    StorageStepRequiredStepNotProvided,
    StorageTransferError,
    StorageTypeInvalidError,
)
from .object import (
    ArtifactImportError,
    ArtifactRevisionEmptyError,
    ArtifactStorageEmptyError,
    ArtifactVerificationFailedError,
    ArtifactVerifyStorageTypeInvalid,
    FileStreamDownloadError,
    FileStreamUploadError,
    HuggingFaceAPIError,
    HuggingFaceModelNotFoundError,
    ObjectInfoFetchError,
    ObjectStorageBucketNotFoundError,
    ObjectStorageConfigInvalidError,
    ObjectStorageObjectDeletionError,
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    RegistryNotFoundError,
    ReservoirStorageConfigInvalidError,
    StorageBucketFileNotFoundError,
)
from .process import (
    CephNotInstalledError,
    DDNCommandFailedError,
    MetricNotFoundError,
    NetAppClientError,
    NetAppQTreeNotFoundError,
    PureStorageCommandFailedError,
    QuotaCommandFailedError,
    SubprocessStdoutNotAvailableError,
)
from .quota import (
    InvalidQuotaConfig,
    InvalidQuotaFormatError,
    InvalidQuotaScopeError,
    QuotaDirectoryNotEmptyError,
    QuotaScopeAlreadyExists,
    QuotaScopeNotFoundError,
    QuotaTreeNotFoundError,
)
from .vfolder import (
    InvalidSubpathError,
    VFolderNotFoundError,
)
from .volume import (
    InvalidVolumeError,
    MetadataTooLargeError,
    VolumeNotInitializedError,
)

__all__ = [
    # base
    "StorageProxyError",
    "ProcessExecutionError",
    "ExternalStorageServiceError",
    "NotImplementedAPI",
    # common
    "InvalidAPIParameters",
    "StorageNotFoundError",
    "StorageTypeInvalidError",
    "StorageTransferError",
    "StorageStepRequiredStepNotProvided",
    "InvalidPathError",
    "InvalidSocketPathError",
    "InvalidConfigurationSourceError",
    "InvalidDataLengthError",
    "ServiceNotInitializedError",
    # vfolder
    "VFolderNotFoundError",
    "InvalidSubpathError",
    # quota
    "QuotaDirectoryNotEmptyError",
    "QuotaScopeNotFoundError",
    "QuotaScopeAlreadyExists",
    "InvalidQuotaConfig",
    "InvalidQuotaScopeError",
    "InvalidQuotaFormatError",
    "QuotaTreeNotFoundError",
    # volume
    "InvalidVolumeError",
    "VolumeNotInitializedError",
    "MetadataTooLargeError",
    # process
    "SubprocessStdoutNotAvailableError",
    "QuotaCommandFailedError",
    "CephNotInstalledError",
    "PureStorageCommandFailedError",
    "NetAppClientError",
    "NetAppQTreeNotFoundError",
    "DDNCommandFailedError",
    "MetricNotFoundError",
    # object
    "FileStreamUploadError",
    "FileStreamDownloadError",
    "PresignedUploadURLGenerationError",
    "PresignedDownloadURLGenerationError",
    "ObjectInfoFetchError",
    "ObjectStorageBucketNotFoundError",
    "StorageBucketFileNotFoundError",
    "ObjectStorageConfigInvalidError",
    "ReservoirStorageConfigInvalidError",
    "ObjectStorageObjectDeletionError",
    "RegistryNotFoundError",
    "HuggingFaceAPIError",
    "HuggingFaceModelNotFoundError",
    "ArtifactStorageEmptyError",
    "ArtifactRevisionEmptyError",
    "ArtifactImportError",
    "ArtifactVerifyStorageTypeInvalid",
    "ArtifactVerificationFailedError",
]
