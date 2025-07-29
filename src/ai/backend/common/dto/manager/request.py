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
