import uuid
from typing import Any

from graphql import GraphQLFormattedError
from graphql.language.location import FormattedSourceLocation
from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .vfolder.response import DeleteFilesAsyncResponse as DeleteFilesAsyncResponse
from .vfolder.response import VFolderCreateResponse as VFolderCreateResponse
from .vfolder.response import VFolderListResponse as VFolderListResponse


class GraphQLResponse(BaseResponseModel):
    """
    Used in V2 API for handling GraphQL requests.
    """

    data: dict[str, Any] | None = Field(
        default=None,
        description="The data returned from the GraphQL query.",
    )
    errors: list[GraphQLFormattedError] | None = Field(
        default=None,
        description="A list of errors that occurred during the GraphQL query.",
    )
    extensions: dict[str, Any] | None = Field(
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


class GetPresignedDownloadURLResponse(BaseResponseModel):
    presigned_url: str = Field(description="The presigned download URL")


class GetPresignedUploadURLResponse(BaseResponseModel):
    presigned_url: str = Field(description="The presigned upload URL")
    # TODO: Remove fields if not needed
    fields: str = Field(description="JSON string containing the form fields")


class ObjectStorageBucketsResponse(BaseResponseModel):
    buckets: list[str] = Field(description="List of bucket names for a specific storage")


class ObjectStorageAllBucketsResponse(BaseResponseModel):
    buckets_by_storage: dict[uuid.UUID, list[str]] = Field(
        description="Mapping of storage IDs to bucket lists"
    )
