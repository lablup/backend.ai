import uuid
from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .vfolder.request import DeleteFilesAsyncBodyParam as DeleteFilesAsyncBodyParam
from .vfolder.request import DeleteFilesAsyncPathParam as DeleteFilesAsyncPathParam
from .vfolder.request import RenameVFolderReq as RenameVFolderReq
from .vfolder.request import VFolderCreateReq as VFolderCreateReq


class GraphQLReq(BaseRequestModel):
    """
    Used in V2 API for handling GraphQL requests.
    """

    query: str = Field(
        description="GraphQL query string, defining the operations to be performed.",
    )
    variables: dict[str, Any] | None = Field(
        default=None,
        description="Variables for the GraphQL query.",
    )
    operation_name: str | None = Field(
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
    description: str | None = Field(default=None, description="Updated description")
    readonly: bool | None = Field(
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
    name: str | None = Field(default=None, description="Updated name of the object storage")
    host: str | None = Field(default=None, description="Updated host address")
    access_key: str | None = Field(default=None, description="Updated access key")
    secret_key: str | None = Field(default=None, description="Updated secret key")
    endpoint: str | None = Field(default=None, description="Updated endpoint URL")
    region: str | None = Field(default=None, description="Updated region")


class CreateHuggingFaceRegistryReq(BaseRequestModel):
    name: str = Field(description="Name of the Hugging Face model registry")
    endpoint: str = Field(
        description="Endpoint URL of the Hugging Face model registry",
        examples=["https://huggingface.co"],
    )
    token: str | None = Field(
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
    expiration: int | None = Field(default=None, description="URL expiration time in seconds")


class GetPresignedUploadURLReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(
        description="The unique identifier of the artifact revision"
    )
    key: str = Field(description="Object key")
    content_type: str | None = Field(default=None, description="Content type of the object")
    expiration: int | None = Field(default=None, description="URL expiration time in seconds")
    min_size: int | None = Field(default=None, description="Minimum file size")
    max_size: int | None = Field(default=None, description="Maximum file size")
