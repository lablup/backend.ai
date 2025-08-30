import uuid
from typing import Any, Optional

from graphql import GraphQLFormattedError
from graphql.language.location import FormattedSourceLocation
from pydantic import Field

from ...api_handlers import BaseResponseModel
from .field import VFolderItemField


class VFolderCreateResponse(BaseResponseModel):
    item: VFolderItemField


class VFolderListResponse(BaseResponseModel):
    items: list[VFolderItemField] = Field(default_factory=list)


class GraphQLResponse(BaseResponseModel):
    """
    Used in V2 API for handling GraphQL requests.
    """

    data: Optional[dict[str, Any]] = Field(
        default=None,
        description="The data returned from the GraphQL query.",
    )
    errors: Optional[list[GraphQLFormattedError]] = Field(
        default=None,
        description="A list of errors that occurred during the GraphQL query.",
    )
    extensions: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional information about the GraphQL response.",
    )


# Ensure that thirdparty's forward-referenced types can be serialized correctly.
GraphQLResponse.model_rebuild(
    _types_namespace={
        "GraphQLFormattedError": GraphQLFormattedError,
        "FormattedSourceLocation": FormattedSourceLocation,
    }
)


# Artifact API Response Models
class ImportArtifactResponse(BaseResponseModel):
    artifact_id: str = Field(description="ID of the imported artifact")
    name: str = Field(description="Name of the artifact")
    version: str = Field(description="Version of the artifact")
    size: int = Field(description="Size of the artifact in bytes")


class UpdateArtifactResponse(BaseResponseModel):
    artifact_id: str = Field(description="ID of the updated artifact")
    name: str = Field(description="Name of the artifact")
    version: str = Field(description="Version of the artifact")


class DeleteArtifactResponse(BaseResponseModel):
    artifact_id: str = Field(description="ID of the deleted artifact")
    message: str = Field(description="Deletion confirmation message")


# ObjectStorage API Response Models
class ObjectStorageResponse(BaseResponseModel):
    id: str = Field(description="ID of the object storage")
    name: str = Field(description="Name of the object storage")
    host: str = Field(description="Host address of the object storage")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    endpoint: str = Field(description="Endpoint URL of the object storage")
    region: str = Field(description="Region of the object storage")


class ObjectStorageListResponse(BaseResponseModel):
    storages: list[ObjectStorageResponse] = Field(description="List of object storages")


class DeleteObjectStorageResponse(BaseResponseModel):
    pass


# Object Storage Presigned URL Response Models
class GetPresignedDownloadURLResponse(BaseResponseModel):
    presigned_url: str = Field(description="The presigned download URL")


class GetPresignedUploadURLResponse(BaseResponseModel):
    presigned_url: str = Field(description="The presigned upload URL")
    fields: str = Field(description="JSON string containing the form fields")


# Object Storage Bucket Response Models
class RegisterObjectStorageBucketResponse(BaseResponseModel):
    id: uuid.UUID = Field(description="The ID of the registered bucket")


class ObjectStorageBucketsResponse(BaseResponseModel):
    buckets: list[str] = Field(description="List of bucket names for a specific storage")


class ObjectStorageAllBucketsResponse(BaseResponseModel):
    buckets_by_storage: dict[uuid.UUID, list[str]] = Field(
        description="Mapping of storage IDs to bucket lists"
    )


# Artifact Installed Storages Response Models
class ArtifactInstalledStoragesResponse(BaseResponseModel):
    installed_storages: dict[uuid.UUID, uuid.UUID] = Field(
        description="Mapping of artifact revision IDs to storage IDs"
    )


class UnregisterObjectStorageBucketResponse(BaseResponseModel):
    id: uuid.UUID = Field(description="The ID of the unregistered bucket")


class ObjectStorageBucketListResponse(BaseResponseModel):
    buckets: list[str] = Field(default_factory=list, description="List of bucket names")


# Association Artifact-Storage API Response Models
class AssociationArtifactStorageResponse(BaseResponseModel):
    id: str = Field(description="ID of the association")
    artifact_id: str = Field(description="ID of the associated artifact")
    storage_id: str = Field(description="ID of the associated storage")


class AssociateArtifactWithStorageResponse(BaseResponseModel):
    association: AssociationArtifactStorageResponse = Field(description="Created association")
    message: str = Field(description="Success message")


class DisassociateArtifactWithStorageResponse(BaseResponseModel):
    association: AssociationArtifactStorageResponse = Field(description="Removed association")
    message: str = Field(description="Success message")
