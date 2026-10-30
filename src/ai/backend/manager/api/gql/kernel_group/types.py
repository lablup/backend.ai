"""Kernel group GraphQL types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Self, cast, override
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupFilter as KernelGroupFilterDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupOrder as KernelGroupOrderDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.response import (
    KernelGroupNode as KernelGroupNodeDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.types import (
    KernelGroupOrderField as KernelGroupOrderFieldDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.common_types import BinarySizeInfoGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.image.types import ImageV2GQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.session.types import SessionV2GQL

__all__ = (
    "KernelGroupConnectionGQL",
    "KernelGroupEdgeGQL",
    "KernelGroupFilterGQL",
    "KernelGroupGQL",
    "KernelGroupOrderByGQL",
)


KernelGroupOrderFieldGQL: type[KernelGroupOrderFieldDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering kernel groups.",
    ),
    KernelGroupOrderFieldDTO,
    name="KernelGroupOrderField",
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One role of a session and the execution spec its kernels share.",
    ),
    name="KernelGroup",
)
class KernelGroupGQL(PydanticNodeMixin[KernelGroupNodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    field_id: UUID = gql_field(description="ID of the kernel group.")
    session_id: UUID = gql_field(description="ID of the session the group belongs to.")
    role: str = gql_field(description="Role of the group, unique within its session.")
    image_id: UUID | None = gql_field(description="ID of the image the group's kernels run.")
    shmem: BinarySizeInfoGQL | None = gql_field(
        description="Shared memory requested for the group. Null means the runtime default."
    )
    startup_command: str | None = gql_field(
        description="Command the group's kernels run at startup."
    )
    preopen_ports: list[int] = gql_field(description="Ports pre-opened on the group's kernels.")
    requested_starts_at: datetime | None = gql_field(
        description="Reserved start time requested at creation. Honored only for batch sessions."
    )
    batch_timeout: int | None = gql_field(description="Batch execution timeout in seconds.")

    @gql_field(description="The session the group belongs to.")  # type: ignore[misc]
    async def session(
        self, info: Info[StrawberryGQLContext]
    ) -> (
        Annotated[SessionV2GQL, strawberry.lazy("ai.backend.manager.api.gql.session.types")] | None
    ):
        return await info.context.data_loaders.session_loader.load(SessionID(self.session_id))

    @gql_field(description="The image the group's kernels run.")  # type: ignore[misc]
    async def image(self, info: Info[StrawberryGQLContext]) -> ImageV2GQL | None:
        if self.image_id is None:
            return None
        return await info.context.data_loaders.image_loader.load(ImageID(self.image_id))

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext, Any],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.kernel_group_loader.load_many([
            KernelGroupID(UUID(node_id)) for node_id in node_ids
        ])
        return cast(list[Self | None], results)


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One kernel group within a connection.",
    ),
    name="KernelGroupEdge",
)
class KernelGroupEdgeGQL(Edge[KernelGroupGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for kernel groups.",
    ),
    name="KernelGroupConnection",
)
class KernelGroupConnectionGQL(Connection[KernelGroupGQL]):
    # Restated so the schema's edge type is the described one above rather than the
    # one Strawberry would generate from the generic, which carries no version.
    edges: list[KernelGroupEdgeGQL] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int = gql_field(description="Total number of kernel groups matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for kernel groups.",
    ),
    name="KernelGroupFilter",
)
class KernelGroupFilterGQL(PydanticInputMixin[KernelGroupFilterDTO]):
    field_id: UUIDFilter | None = gql_field(description="Filter by kernel group ID.", default=None)
    role: StringFilter | None = gql_field(description="Filter by role.", default=None)
    image_id: UUIDFilter | None = gql_field(description="Filter by image ID.", default=None)
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by creation time.", default=None
    )
    AND: list[Self] | None = gql_field(description="Match all nested filters.", default=None)
    OR: list[Self] | None = gql_field(description="Match any nested filter.", default=None)
    NOT: list[Self] | None = gql_field(description="Negate nested filters.", default=None)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One ordering rule for a kernel group search.",
    ),
    name="KernelGroupOrderBy",
)
class KernelGroupOrderByGQL(PydanticInputMixin[KernelGroupOrderDTO]):
    field: KernelGroupOrderFieldGQL = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )
