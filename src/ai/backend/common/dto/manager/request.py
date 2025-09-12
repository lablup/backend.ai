import uuid
from typing import Any, Optional

from pydantic import AliasChoices, Field

from ...api_handlers import BaseRequestModel
from ...typed_validators import VFolderName
from ...types import VFolderUsageMode
from .field import VFolderPermissionField


class VFolderCreateReq(BaseRequestModel):
    name: VFolderName = Field(description="Name of the vfolder")
    folder_host: Optional[str] = Field(default=None, alias="host")
    usage_mode: VFolderUsageMode = Field(default=VFolderUsageMode.GENERAL)
    permission: VFolderPermissionField = Field(default=VFolderPermissionField.READ_WRITE)
    unmanaged_path: Optional[str] = Field(default=None, alias="unmanagedPath")
    group_id: Optional[uuid.UUID] = Field(
        default=None,
        validation_alias=AliasChoices("group", "groupId"),
    )
    cloneable: bool = Field(default=False)


class RenameVFolderReq(BaseRequestModel):
    new_name: VFolderName = Field(description="Name of the vfolder")


class GraphQLReq(BaseRequestModel):
    """
    Used in V2 API for handling GraphQL requests.
    """

    query: str = Field(
        description="GraphQL query string, defining the operations to be performed.",
    )
    variables: Optional[dict[str, Any]] = Field(
        default=None,
        description="Variables for the GraphQL query.",
    )
    operation_name: Optional[str] = Field(
        default=None,
        alias="operationName",
    )


# Artifact API Request Models
class ImportArtifactPathParam(BaseRequestModel):
    artifact_id: uuid.UUID = Field(
        description="The unique identifier of the artifact to be imported."
    )


class ImportArtifactReq(BaseRequestModel):
    storage_id: uuid.UUID = Field(
        description="The unique identifier of the storage where the artifact will be imported."
    )


class UpdateArtifactPathParam(BaseRequestModel):
    artifact_id: uuid.UUID = Field(
        description="The unique identifier of the artifact to be updated."
    )


class UpdateArtifactReq(BaseRequestModel):
    description: Optional[str] = Field(default=None, description="Updated description")
    readonly: Optional[bool] = Field(
        default=None, description="Whether the artifact should be readonly."
    )


class DeleteArtifactPathParam(BaseRequestModel):
    artifact_id: uuid.UUID = Field(
        description="The unique identifier of the artifact to be deleted."
    )


class CreateObjectStorageReq(BaseRequestModel):
    name: str = Field(description="Name of the object storage")
    host: str = Field(description="Host address of the object storage")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    endpoint: str = Field(description="Endpoint URL of the object storage")
    region: str = Field(description="Region of the object storage")


class ObjectStoragePathParam(BaseRequestModel):
    storage_id: uuid.UUID = Field(description="The unique identifier of the object storage.")


class UpdateObjectStorageReq(BaseRequestModel):
    name: Optional[str] = Field(default=None, description="Updated name of the object storage")
    host: Optional[str] = Field(default=None, description="Updated host address")
    access_key: Optional[str] = Field(default=None, description="Updated access key")
    secret_key: Optional[str] = Field(default=None, description="Updated secret key")
    endpoint: Optional[str] = Field(default=None, description="Updated endpoint URL")
    region: Optional[str] = Field(default=None, description="Updated region")


class CreateHuggingFaceRegistryReq(BaseRequestModel):
    name: str = Field(description="Name of the Hugging Face model registry")
    endpoint: str = Field(
        description="Endpoint URL of the Hugging Face model registry",
        examples=["https://huggingface.co"],
    )
    token: Optional[str] = Field(
        description="Authentication token for the Hugging Face model registry",
        examples=["your_token_here"],
    )


class DeleteHuggingFaceRegistryReq(BaseRequestModel):
    id: uuid.UUID = Field(description="The unique identifier of the Hugging Face model registry")


class GetPresignedDownloadURLReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(
        description="The unique identifier of the artifact revision"
    )
    key: str = Field(description="Object key")
    expiration: Optional[int] = Field(default=None, description="URL expiration time in seconds")


class GetPresignedUploadURLReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(
        description="The unique identifier of the artifact revision"
    )
    key: str = Field(description="Object key")
    content_type: Optional[str] = Field(default=None, description="Content type of the object")
    expiration: Optional[int] = Field(default=None, description="URL expiration time in seconds")
    min_size: Optional[int] = Field(default=None, description="Minimum file size")
    max_size: Optional[int] = Field(default=None, description="Maximum file size")
