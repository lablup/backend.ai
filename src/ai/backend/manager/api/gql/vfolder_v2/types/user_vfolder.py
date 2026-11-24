"""GraphQL types for one user paired with one virtual folder."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self, override
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.vfolder.request import UserVFolderFilter, UserVFolderOrder
from ai.backend.common.dto.manager.v2.vfolder.response import UserVFolderNode
from ai.backend.common.dto.manager.v2.vfolder.types import (
    UserVFolderScope,
    VFolderMountPermissionFilter,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, UUIDScopeGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_resolver,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder_v2.types.enum import VFolderMountPermissionGQL
from ai.backend.manager.api.gql.vfolder_v2.types.filters import (
    VFolderFilterGQL,
    VFolderOrderFieldGQL,
)
from ai.backend.manager.errors.api import NotImplementedAPI

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL
    from ai.backend.manager.api.gql.vfolder_v2.types.node import VFolderGQL


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One user paired with one virtual folder.",
    ),
    name="UserVFolder",
)
class UserVFolderGQL(PydanticNodeMixin[UserVFolderNode]):
    id: NodeID[str]
    user_id: UUID = gql_field(description="ID of the user.")
    vfolder_id: UUID = gql_field(description="ID of the virtual folder.")
    mount_permission: VFolderMountPermissionGQL = gql_field(
        description=(
            "Mount policy of the user on the virtual folder: NONE without read access, READ_WRITE "
            "on a personal folder they own, otherwise their own mount policy or the folder's "
            "default."
        )
    )

    @gql_resolver(description="The user.")
    async def user(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.user_loader.load(UserID(self.user_id))

    @gql_resolver(description="The virtual folder.")
    async def vfolder(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            VFolderGQL,
            strawberry.lazy("ai.backend.manager.api.gql.vfolder_v2.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.vfolder_loader.load(VFolderUUID(self.vfolder_id))

    @classmethod
    @override
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Self]:
        raise NotImplementedAPI("User vfolder node resolution is not implemented.")


UserVFolderEdgeGQL = Edge[UserVFolderGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for pairs of a user and a virtual folder.",
    ),
    name="UserVFolderConnection",
)
class UserVFolderConnectionGQL(Connection[UserVFolderGQL]):
    count: int = gql_field(description="Total number of pairs matching the query criteria.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Scope for the scoped user virtual folder query: one user, and the virtual folders "
            "paired with them. The folders of the user, the domains and the projects are OR'd, "
            "and every scope named is authorized before the read runs."
        ),
    ),
    name="UserVFolderScope",
)
class UserVFolderScopeGQL(PydanticInputMixin[UserVFolderScope]):
    user: list[UUIDScopeGQL] = gql_field(
        description="The user paired with each folder, exactly one. Their folders are read too."
    )
    domain: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Domains whose vfolders are being read."
    )
    project: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Projects whose vfolders are being read."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Filter for the mount policy of a user on a virtual folder. "
            "RW_DELETE matches READ_WRITE."
        ),
    ),
    name="VFolderMountPermissionFilter",
)
class VFolderMountPermissionFilterGQL(PydanticInputMixin[VFolderMountPermissionFilter]):
    equals: VFolderMountPermissionGQL | None = gql_field(description="Exact match.", default=None)
    in_: list[VFolderMountPermissionGQL] | None = gql_field(
        description="Match any of the given levels.", name="in", default=None
    )
    not_equals: VFolderMountPermissionGQL | None = gql_field(
        description="Exclude an exact match.", default=None
    )
    not_in: list[VFolderMountPermissionGQL] | None = gql_field(
        description="Exclude any of the given levels.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for pairs of a user and a virtual folder.",
    ),
    name="UserVFolderFilter",
)
class UserVFolderFilterGQL(PydanticInputMixin[UserVFolderFilter]):
    mount_permission: VFolderMountPermissionFilterGQL | None = gql_field(
        description="Filter by the mount policy of the user on the folder.", default=None
    )
    vfolder: VFolderFilterGQL | None = gql_field(
        description="Filter by the folder of the pair.", default=None
    )

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Ordering for pairs of a user and a virtual folder, by the folder of the pair.",
    ),
    name="UserVFolderOrderBy",
)
class UserVFolderOrderByGQL(PydanticInputMixin[UserVFolderOrder]):
    field: VFolderOrderFieldGQL = VFolderOrderFieldGQL.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
