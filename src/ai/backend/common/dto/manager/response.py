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
