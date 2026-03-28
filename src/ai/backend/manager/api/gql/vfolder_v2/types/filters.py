"""VFolder V2 GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.vfolder.request import VFolderV2Filter, VFolderV2Order
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderStatusFilter,
    VFolderUsageModeFilter,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "VFolder operation status. "
            "READY: Folder is ready for use. "
            "CLONING: Folder is being cloned. "
            "DELETE_PENDING: Folder is in trash bin (recoverable). "
            "DELETE_ONGOING: Deletion is in progress. "
            "DELETE_COMPLETE: Deletion is complete. "
            "DELETE_ERROR: An error occurred during deletion."
        ),
    ),
    name="VFolderV2OperationStatus",
)
class VFolderV2OperationStatusGQL(StrEnum):
    READY = "ready"
    CLONING = "cloning"
    DELETE_PENDING = "delete-pending"
    DELETE_ONGOING = "delete-ongoing"
    DELETE_COMPLETE = "delete-complete"
    DELETE_ERROR = "delete-error"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "VFolder usage mode. "
            "GENERAL: Normal virtual folder. "
            "MODEL: Virtual folder for shared models. "
            "DATA: Virtual folder for shared data."
        ),
    ),
    name="VFolderV2UsageMode",
)
class VFolderV2UsageModeGQL(StrEnum):
    GENERAL = "general"
    MODEL = "model"
    DATA = "data"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for VFolder operation status enum fields. Supports in and not_in operations.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderV2OperationStatusFilter",
)
class VFolderV2OperationStatusFilterGQL(PydanticInputMixin[VFolderStatusFilter]):
    """Filter for vfolder operation status enum fields."""

    in_: list[VFolderV2OperationStatusGQL] | None = gql_field(
        description="The in field.", name="in", default=None
    )
    not_in: list[VFolderV2OperationStatusGQL] | None = gql_field(
        description="Exclude statuses not in this list.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for VFolder usage mode enum fields. Supports in and not_in operations.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderV2UsageModeFilter",
)
class VFolderV2UsageModeFilterGQL(PydanticInputMixin[VFolderUsageModeFilter]):
    """Filter for vfolder usage mode enum fields."""

    in_: list[VFolderV2UsageModeGQL] | None = gql_field(
        description="The in field.", name="in", default=None
    )
    not_in: list[VFolderV2UsageModeGQL] | None = gql_field(
        description="Exclude usage modes not in this list.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying virtual folders. Supports filtering by name, host, status, usage mode, and creation time. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderV2Filter",
)
class VFolderV2FilterGQL(PydanticInputMixin[VFolderV2Filter]):
    """Filter for vfolder queries."""

    name: StringFilter | None = None
    host: StringFilter | None = None
    status: VFolderV2OperationStatusFilterGQL | None = None
    usage_mode: VFolderV2UsageModeFilterGQL | None = None
    created_at: DateTimeFilter | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Fields available for ordering virtual folder query results. "
            "NAME: Order by folder name alphabetically. "
            "CREATED_AT: Order by creation timestamp. "
            "STATUS: Order by operation status. "
            "USAGE_MODE: Order by usage mode. "
            "HOST: Order by storage host."
        ),
    ),
    name="VFolderV2OrderField",
)
class VFolderV2OrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    STATUS = "status"
    USAGE_MODE = "usage_mode"
    HOST = "host"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for virtual folder query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderV2OrderBy",
)
class VFolderV2OrderByGQL(PydanticInputMixin[VFolderV2Order]):
    """OrderBy for vfolder queries."""

    field: VFolderV2OrderFieldGQL = VFolderV2OrderFieldGQL.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
