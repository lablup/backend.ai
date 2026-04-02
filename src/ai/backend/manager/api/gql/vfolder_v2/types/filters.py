"""VFolder GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.vfolder.request import VFolderFilter, VFolderOrder
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

from .enum import VFolderOperationStatusGQL, VFolderUsageModeGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for VFolder operation status enum fields. Supports in and not_in operations.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderOperationStatusFilter",
)
class VFolderOperationStatusFilterGQL(PydanticInputMixin[VFolderStatusFilter]):
    """Filter for vfolder operation status enum fields."""

    in_: list[VFolderOperationStatusGQL] | None = gql_field(
        description="The in field.", name="in", default=None
    )
    not_in: list[VFolderOperationStatusGQL] | None = gql_field(
        description="Exclude statuses not in this list.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for VFolder usage mode enum fields. Supports in and not_in operations.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderUsageModeFilter",
)
class VFolderUsageModeFilterGQL(PydanticInputMixin[VFolderUsageModeFilter]):
    """Filter for vfolder usage mode enum fields."""

    in_: list[VFolderUsageModeGQL] | None = gql_field(
        description="The in field.", name="in", default=None
    )
    not_in: list[VFolderUsageModeGQL] | None = gql_field(
        description="Exclude usage modes not in this list.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying virtual folders. Supports filtering by name, host, status, usage mode, and creation time. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderFilter",
)
class VFolderFilterGQL(PydanticInputMixin[VFolderFilter]):
    """Filter for vfolder queries."""

    name: StringFilter | None = None
    host: StringFilter | None = None
    status: VFolderOperationStatusFilterGQL | None = None
    usage_mode: VFolderUsageModeFilterGQL | None = None
    cloneable: bool | None = None
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
    name="VFolderOrderField",
)
class VFolderOrderFieldGQL(StrEnum):
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
    name="VFolderOrderBy",
)
class VFolderOrderByGQL(PydanticInputMixin[VFolderOrder]):
    """OrderBy for vfolder queries."""

    field: VFolderOrderFieldGQL = VFolderOrderFieldGQL.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
