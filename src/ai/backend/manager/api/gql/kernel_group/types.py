"""Kernel group GraphQL types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, Any, Self, cast, override
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironID
from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.query import UUIDFilter as UUIDFilterDTO
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupEnvironFilter as KernelGroupEnvironFilterDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupEnvironNestedFilter as KernelGroupEnvironNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupEnvironOrder as KernelGroupEnvironOrderDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupFilter as KernelGroupFilterDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupOrder as KernelGroupOrderDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupResourceSlotFilter as KernelGroupResourceSlotFilterDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupResourceSlotNestedFilter as KernelGroupResourceSlotNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupResourceSlotOrder as KernelGroupResourceSlotOrderDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    ScopedSearchKernelGroupEnvironsInput,
    ScopedSearchKernelGroupResourceSlotsInput,
)
from ai.backend.common.dto.manager.v2.kernel_group.response import (
    KernelGroupEnvironNode as KernelGroupEnvironNodeDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.response import (
    KernelGroupNode as KernelGroupNodeDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.response import (
    KernelGroupResourceSlotNode as KernelGroupResourceSlotNodeDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.types import (
    KernelGroupEnvironOrderField as KernelGroupEnvironOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.types import (
    KernelGroupEnvironScope,
    KernelGroupResourceSlotScope,
)
from ai.backend.common.dto.manager.v2.kernel_group.types import (
    KernelGroupOrderField as KernelGroupOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.kernel_group.types import (
    KernelGroupResourceSlotOrderField as KernelGroupResourceSlotOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    DecimalFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
    encode_cursor,
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
    "KernelGroupEnvironConnectionGQL",
    "KernelGroupEnvironEdgeGQL",
    "KernelGroupEnvironFilterGQL",
    "KernelGroupEnvironGQL",
    "KernelGroupEnvironNestedFilterGQL",
    "KernelGroupEnvironOrderByGQL",
    "KernelGroupFilterGQL",
    "KernelGroupGQL",
    "KernelGroupOrderByGQL",
    "KernelGroupResourceSlotConnectionGQL",
    "KernelGroupResourceSlotEdgeGQL",
    "KernelGroupResourceSlotFilterGQL",
    "KernelGroupResourceSlotGQL",
    "KernelGroupResourceSlotNestedFilterGQL",
    "KernelGroupResourceSlotOrderByGQL",
)


KernelGroupOrderFieldGQL: type[KernelGroupOrderFieldDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering kernel groups.",
    ),
    KernelGroupOrderFieldDTO,
    name="KernelGroupOrderField",
)

KernelGroupEnvironOrderFieldGQL: type[KernelGroupEnvironOrderFieldDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering kernel group environ rows.",
    ),
    KernelGroupEnvironOrderFieldDTO,
    name="KernelGroupEnvironOrderField",
)


KernelGroupResourceSlotOrderFieldGQL: type[KernelGroupResourceSlotOrderFieldDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering kernel group resource slot rows.",
    ),
    KernelGroupResourceSlotOrderFieldDTO,
    name="KernelGroupResourceSlotOrderField",
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One environment variable requested on a kernel group.",
    ),
    name="KernelGroupEnviron",
)
class KernelGroupEnvironGQL(PydanticNodeMixin[KernelGroupEnvironNodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    field_id: UUID = gql_field(description="ID of the environ row.")
    kernel_group_id: UUID = gql_field(description="ID of the kernel group the row belongs to.")
    key: str = gql_field(description="Variable name.")
    value: str = gql_field(description="Variable value.")

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext, Any],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.kernel_group_environ_loader.load_many([
            KernelGroupEnvironID(UUID(node_id)) for node_id in node_ids
        ])
        return cast(list[Self | None], results)


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One kernel group environ row within a connection.",
    ),
    name="KernelGroupEnvironEdge",
)
class KernelGroupEnvironEdgeGQL(Edge[KernelGroupEnvironGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for kernel group environ rows.",
    ),
    name="KernelGroupEnvironConnection",
)
class KernelGroupEnvironConnectionGQL(Connection[KernelGroupEnvironGQL]):
    # Restated so the schema's edge type is the described one above rather than the
    # one Strawberry would generate from the generic, which carries no version.
    edges: list[KernelGroupEnvironEdgeGQL] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int = gql_field(description="Total number of environ rows matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for kernel group environ rows.",
    ),
    name="KernelGroupEnvironFilter",
)
class KernelGroupEnvironFilterGQL(PydanticInputMixin[KernelGroupEnvironFilterDTO]):
    field_id: UUIDFilter | None = gql_field(description="Filter by environ row ID.", default=None)
    kernel_group_id: UUIDFilter | None = gql_field(
        description="Filter by the kernel group the row belongs to.", default=None
    )
    key: StringFilter | None = gql_field(description="Filter by variable name.", default=None)
    AND: list[Self] | None = gql_field(description="Match all nested filters.", default=None)
    OR: list[Self] | None = gql_field(description="Match any nested filter.", default=None)
    NOT: list[Self] | None = gql_field(description="Negate nested filters.", default=None)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One ordering rule for a kernel group environ search.",
    ),
    name="KernelGroupEnvironOrderBy",
)
class KernelGroupEnvironOrderByGQL(PydanticInputMixin[KernelGroupEnvironOrderDTO]):
    field: KernelGroupEnvironOrderFieldGQL = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One slot's amount requested on each kernel of a kernel group.",
    ),
    name="KernelGroupResourceSlot",
)
class KernelGroupResourceSlotGQL(PydanticNodeMixin[KernelGroupResourceSlotNodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    field_id: UUID = gql_field(description="ID of the resource slot row.")
    kernel_group_id: UUID = gql_field(description="ID of the kernel group the row belongs to.")
    slot_name: str = gql_field(description="Resource slot name (e.g. cpu, mem).")
    quantity: Decimal = gql_field(description="Amount requested on each kernel of the group.")

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext, Any],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.kernel_group_resource_slot_loader.load_many([
            KernelGroupResourceSlotID(UUID(node_id)) for node_id in node_ids
        ])
        return cast(list[Self | None], results)


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One kernel group resource slot row within a connection.",
    ),
    name="KernelGroupResourceSlotEdge",
)
class KernelGroupResourceSlotEdgeGQL(Edge[KernelGroupResourceSlotGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for kernel group resource slot rows.",
    ),
    name="KernelGroupResourceSlotConnection",
)
class KernelGroupResourceSlotConnectionGQL(Connection[KernelGroupResourceSlotGQL]):
    # Restated so the schema's edge type is the described one above rather than the
    # one Strawberry would generate from the generic, which carries no version.
    edges: list[KernelGroupResourceSlotEdgeGQL] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int = gql_field(description="Total number of resource slot rows matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for kernel group resource slot rows.",
    ),
    name="KernelGroupResourceSlotFilter",
)
class KernelGroupResourceSlotFilterGQL(PydanticInputMixin[KernelGroupResourceSlotFilterDTO]):
    field_id: UUIDFilter | None = gql_field(
        description="Filter by resource slot row ID.", default=None
    )
    kernel_group_id: UUIDFilter | None = gql_field(
        description="Filter by the kernel group the row belongs to.", default=None
    )
    slot_name: StringFilter | None = gql_field(description="Filter by slot name.", default=None)
    quantity: DecimalFilter | None = gql_field(
        description="Filter by the amount requested on each kernel.", default=None
    )
    AND: list[Self] | None = gql_field(description="Match all nested filters.", default=None)
    OR: list[Self] | None = gql_field(description="Match any nested filter.", default=None)
    NOT: list[Self] | None = gql_field(description="Negate nested filters.", default=None)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One ordering rule for a kernel group resource slot search.",
    ),
    name="KernelGroupResourceSlotOrderBy",
)
class KernelGroupResourceSlotOrderByGQL(PydanticInputMixin[KernelGroupResourceSlotOrderDTO]):
    field: KernelGroupResourceSlotOrderFieldGQL = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
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

    @gql_field(description="Environment variables requested on the group.")  # type: ignore[misc]
    async def environ(
        self,
        info: Info[StrawberryGQLContext],
        filter: KernelGroupEnvironFilterGQL | None = None,
        order_by: list[KernelGroupEnvironOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> KernelGroupEnvironConnectionGQL | None:
        payload = await info.context.adapters.session.scoped_search_kernel_group_environs(
            ScopedSearchKernelGroupEnvironsInput(
                scope=KernelGroupEnvironScope(session=[UUIDScope(value=self.session_id)]),
                filter=KernelGroupEnvironFilterDTO(
                    kernel_group_id=UUIDFilterDTO(equals=self.field_id),
                    AND=[filter.to_pydantic()] if filter else None,
                ),
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            )
        )
        nodes = [KernelGroupEnvironGQL.from_pydantic(item) for item in payload.items]
        edges = [
            KernelGroupEnvironEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes
        ]
        return KernelGroupEnvironConnectionGQL(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @gql_field(description="Resource slots requested on each kernel of the group.")  # type: ignore[misc]
    async def resource_slots(
        self,
        info: Info[StrawberryGQLContext],
        filter: KernelGroupResourceSlotFilterGQL | None = None,
        order_by: list[KernelGroupResourceSlotOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> KernelGroupResourceSlotConnectionGQL | None:
        payload = await info.context.adapters.session.scoped_search_kernel_group_resource_slots(
            ScopedSearchKernelGroupResourceSlotsInput(
                scope=KernelGroupResourceSlotScope(session=[UUIDScope(value=self.session_id)]),
                filter=KernelGroupResourceSlotFilterDTO(
                    kernel_group_id=UUIDFilterDTO(equals=self.field_id),
                    AND=[filter.to_pydantic()] if filter else None,
                ),
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            )
        )
        nodes = [KernelGroupResourceSlotGQL.from_pydantic(item) for item in payload.items]
        edges = [
            KernelGroupResourceSlotEdgeGQL(node=node, cursor=encode_cursor(node.id))
            for node in nodes
        ]
        return KernelGroupResourceSlotConnectionGQL(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

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
        description="Filter kernel groups by conditions on their environ rows.",
    ),
    name="KernelGroupEnvironNestedFilter",
)
class KernelGroupEnvironNestedFilterGQL(PydanticInputMixin[KernelGroupEnvironNestedFilterDTO]):
    exists: bool | None = gql_field(
        description=(
            "Matches groups with at least one environ row when true, and groups with none when "
            "false. Says nothing about what the rows hold."
        ),
        default=None,
    )
    some: KernelGroupEnvironFilterGQL | None = gql_field(
        description="Matches groups with at least one environ row satisfying all conditions.",
        default=None,
    )
    every: KernelGroupEnvironFilterGQL | None = gql_field(
        description=(
            "Matches groups where every environ row satisfies all conditions "
            "(also true when the group has none)."
        ),
        default=None,
    )
    none: KernelGroupEnvironFilterGQL | None = gql_field(
        description="Matches groups with no environ row satisfying all conditions.",
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter kernel groups by conditions on their resource slot rows.",
    ),
    name="KernelGroupResourceSlotNestedFilter",
)
class KernelGroupResourceSlotNestedFilterGQL(
    PydanticInputMixin[KernelGroupResourceSlotNestedFilterDTO]
):
    exists: bool | None = gql_field(
        description=(
            "Matches groups with at least one resource slot row when true, and groups with none when "
            "false. Says nothing about what the rows hold."
        ),
        default=None,
    )
    some: KernelGroupResourceSlotFilterGQL | None = gql_field(
        description="Matches groups with at least one resource slot row satisfying all conditions.",
        default=None,
    )
    every: KernelGroupResourceSlotFilterGQL | None = gql_field(
        description=(
            "Matches groups where every resource slot row satisfies all conditions "
            "(also true when the group has none)."
        ),
        default=None,
    )
    none: KernelGroupResourceSlotFilterGQL | None = gql_field(
        description="Matches groups with no resource slot row satisfying all conditions.",
        default=None,
    )


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
    environ: KernelGroupEnvironNestedFilterGQL | None = gql_field(
        description="Filter by conditions on the group's environ rows.", default=None
    )
    resource_slots: KernelGroupResourceSlotNestedFilterGQL | None = gql_field(
        description="Filter by conditions on the group's resource slot rows.", default=None
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
