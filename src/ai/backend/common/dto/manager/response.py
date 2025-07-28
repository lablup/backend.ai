from typing import Any, Optional

from graphql import GraphQLFormattedError
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
