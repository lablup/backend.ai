from typing import Optional

from pydantic import Field

from ...api_handlers import BaseRequestModel
from ...types import QuotaConfig, VFolderID


class QuotaScopeReq(BaseRequestModel):
    options: Optional[QuotaConfig] = Field(
        default=None,
        description="The options for the quota scope.",
    )


class GetVFolderMetaReq(BaseRequestModel):
    subpath: str = Field(
        description="The subpath of the virtual folder.",
    )


class CloneVFolderReq(BaseRequestModel):
    dst_vfolder_id: VFolderID = Field(
        description="The destination virtual folder ID.",
        alias="dst_vfid",
    )


class ObjectStorageAPIPathParams(BaseRequestModel):
    storage_name: str = Field(
        description="The name of the storage configuration to use for the operation."
    )
    bucket_name: str = Field(description="The name of the S3 bucket to operate on.")


class UploadObjectReq(BaseRequestModel):
    """
    Data model for file upload requests to object storage.
    This is used to specify the target bucket and key for the file upload.
    """

    key: str = Field(description="The object key (path) within the bucket to upload the file to.")
    content_type: Optional[str] = Field(
        default=None, description="MIME type of the file being uploaded."
    )
    content_length: Optional[int] = Field(
        default=None, ge=0, description="Total content length of the file being uploaded."
    )


class DownloadObjectReq(BaseRequestModel):
    """
    Data model for file download requests from object storage.
    """

    key: str = Field(description="The object key (path) within the bucket to upload the file to.")


class PresignedUploadObjectReq(BaseRequestModel):
    """
    Data model for generating presigned upload URLs for object storage operations.
    This is used to specify the target bucket, key, and optional parameters for the presigned
    """

    key: str = Field(description="The object key (path) within the bucket to upload the file to.")
    content_type: Optional[str] = Field(
        default=None, description="MIME type of the file being uploaded."
    )
    expiration: Optional[int] = Field(
        default=None, gt=0, description="Token expiration time in seconds"
    )
    min_size: Optional[int] = Field(
        default=None, ge=0, description="Minimum allowed size in bytes for upload operations"
    )
    max_size: Optional[int] = Field(
        default=None, gt=0, description="Maximum allowed size in bytes for upload operations"
    )


class PresignedDownloadObjectReq(BaseRequestModel):
    """
    Data model for generating presigned download URLs for object storage operations.
    """

    key: str = Field(
        description="The object key (path) within the bucket to download the file from."
    )


class GetObjectMetaReq(BaseRequestModel):
    """
    Data model for retrieving metadata of a file in object storage.
    This is used to specify the target bucket and key for the file metadata retrieval.
    """

    key: str = Field(
        description="The object key (path) within the bucket to retrieve metadata for."
    )


class DeleteObjectReq(BaseRequestModel):
    """
    Data model for deleting a file in object storage.
    This is used to specify the target bucket and key for the file deletion.
    """

    key: str = Field(description="The object key (path) within the bucket to delete the file from.")
