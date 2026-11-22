"""GraphQL types for compute clusters. The kubeconfig is input-only."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, cast, override
from uuid import UUID

from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    ComputeClusterFilter as ComputeClusterFilterDTO,
)
from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    ComputeClusterOrder as ComputeClusterOrderDTO,
)
from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    CreateComputeClusterInput as CreateComputeClusterInputDTO,
)
from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    UpdateComputeClusterInput as UpdateComputeClusterInputDTO,
)
from ai.backend.common.dto.manager.v2.compute_cluster.response import ComputeClusterNode
from ai.backend.common.dto.manager.v2.compute_cluster.response import (
    CreateComputeClusterPayload as CreateComputeClusterPayloadDTO,
)
from ai.backend.common.dto.manager.v2.compute_cluster.response import (
    PurgeComputeClusterPayload as PurgeComputeClusterPayloadDTO,
)
from ai.backend.common.dto.manager.v2.compute_cluster.response import (
    UpdateComputeClusterPayload as UpdateComputeClusterPayloadDTO,
)
from ai.backend.common.dto.manager.v2.compute_cluster.types import (
    ComputeClusterStatusFilter as ComputeClusterStatusFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

__all__ = (
    "ComputeClusterConnectionGQL",
    "ComputeClusterEdgeGQL",
    "ComputeClusterFilterGQL",
    "ComputeClusterGQL",
    "ComputeClusterOrderByGQL",
    "ComputeClusterOrderFieldGQL",
    "ComputeClusterStatusFilterGQL",
    "ComputeClusterStatusGQL",
    "CreateComputeClusterInputGQL",
    "CreateComputeClusterPayloadGQL",
    "PurgeComputeClusterPayloadGQL",
    "UpdateComputeClusterInputGQL",
    "UpdateComputeClusterPayloadGQL",
)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Whether the manager reaches a compute cluster's API server.",
    ),
    name="ComputeClusterStatus",
)
class ComputeClusterStatusGQL(StrEnum):
    UNKNOWN = "UNKNOWN"
    ALIVE = "ALIVE"
    LOST = "LOST"


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A Kubernetes cluster that runs the sessions of Kubernetes-backed resource groups. "
            "The kubeconfig is never returned."
        ),
    ),
    name="ComputeCluster",
)
class ComputeClusterGQL(PydanticNodeMixin[ComputeClusterNode]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    entity_id: UUID = gql_field(description="UUID of the compute cluster.")
    name: str = gql_field(description="Unique compute cluster name.")
    description: str | None = gql_field(description="Optional description.")
    api_server: str = gql_field(description="URL of the cluster's Kubernetes API server.")
    namespace_prefix: str = gql_field(
        description="Prefix of the namespaces created in the cluster."
    )
    gateway_addr: str | None = gql_field(description="Address of the cluster's network gateway.")
    gateway_public_key: str | None = gql_field(description="Public key of the cluster's gateway.")
    status: ComputeClusterStatusGQL = gql_field(
        description="Whether the cluster's API server is reachable."
    )
    status_changed_at: datetime | None = gql_field(description="When the status last changed.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last modification timestamp.")

    @classmethod
    @override
    async def resolve_nodes(
        cls,
        *,
        info: Info[StrawberryGQLContext, Any],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self]:
        check_admin_only()
        results = await info.context.data_loaders.compute_cluster_loader.load_many([
            ComputeClusterID(UUID(node_id)) for node_id in node_ids
        ])
        return cast(list[Self], results)


ComputeClusterEdgeGQL = Edge[ComputeClusterGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for compute clusters.",
    ),
    name="ComputeClusterConnection",
)
class ComputeClusterConnectionGQL(Connection[ComputeClusterGQL]):
    count: int = gql_field(description="Total number of compute clusters matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for compute cluster status with equality and membership operators.",
    ),
    name="ComputeClusterStatusFilter",
)
class ComputeClusterStatusFilterGQL(PydanticInputMixin[ComputeClusterStatusFilterDTO]):
    equals: ComputeClusterStatusGQL | None = gql_field(description="Exact match.", default=None)
    in_: list[ComputeClusterStatusGQL] | None = gql_field(
        description="Match any of the provided values.", name="in", default=None
    )
    not_equals: ComputeClusterStatusGQL | None = gql_field(
        description="Exclude an exact match.", default=None
    )
    not_in: list[ComputeClusterStatusGQL] | None = gql_field(
        description="Exclude any of the provided values.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter input for querying compute clusters.",
    ),
    name="ComputeClusterFilter",
)
class ComputeClusterFilterGQL(PydanticInputMixin[ComputeClusterFilterDTO]):
    entity_id: UUIDFilter | None = gql_field(
        description="Filter by compute cluster ID.", default=None
    )
    name: StringFilter | None = gql_field(description="Filter by name.", default=None)
    status: ComputeClusterStatusFilterGQL | None = gql_field(
        description="Filter by status.", default=None
    )
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by creation datetime.", default=None
    )
    AND: list[Self] | None = gql_field(
        description="Match all of the given sub-filters.", default=None
    )
    OR: list[Self] | None = gql_field(
        description="Match any of the given sub-filters.", default=None
    )
    NOT: list[Self] | None = gql_field(description="Negate the given sub-filters.", default=None)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering compute cluster results.",
    ),
    name="ComputeClusterOrderField",
)
class ComputeClusterOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for compute cluster results.",
    ),
    name="ComputeClusterOrderBy",
)
class ComputeClusterOrderByGQL(PydanticInputMixin[ComputeClusterOrderDTO]):
    field: ComputeClusterOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for registering a compute cluster.",
    ),
    name="CreateComputeClusterInput",
)
class CreateComputeClusterInputGQL(PydanticInputMixin[CreateComputeClusterInputDTO]):
    name: str = gql_field(description="Unique compute cluster name.")
    api_server: str = gql_field(description="URL of the cluster's Kubernetes API server.")
    kubeconfig: str = gql_field(
        description="Kubeconfig the manager uses to reach the cluster. Stored encrypted."
    )
    description: str | None = gql_field(default=None, description="Optional description.")
    namespace_prefix: str = gql_field(
        default="bai-", description="Prefix of the namespaces created in the cluster."
    )
    gateway_addr: str | None = gql_field(
        default=None, description="Address of the cluster's network gateway."
    )
    gateway_public_key: str | None = gql_field(
        default=None, description="Public key of the cluster's gateway."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for compute cluster creation.",
    ),
    model=CreateComputeClusterPayloadDTO,
    name="CreateComputeClusterPayload",
)
class CreateComputeClusterPayloadGQL(PydanticOutputMixin[CreateComputeClusterPayloadDTO]):
    compute_cluster: ComputeClusterGQL = gql_field(description="The created compute cluster.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating a compute cluster. Only provided fields are updated.",
    ),
    name="UpdateComputeClusterInput",
)
class UpdateComputeClusterInputGQL(PydanticInputMixin[UpdateComputeClusterInputDTO]):
    description: str | None = gql_field(
        default=UNSET, description="Updated description. Null clears it."
    )
    api_server: str | None = gql_field(default=UNSET, description="Updated API server URL.")
    kubeconfig: str | None = gql_field(
        default=UNSET, description="Replacement kubeconfig. Stored encrypted."
    )
    namespace_prefix: str | None = gql_field(default=UNSET, description="Updated namespace prefix.")
    gateway_addr: str | None = gql_field(
        default=UNSET, description="Updated gateway address. Null clears it."
    )
    gateway_public_key: str | None = gql_field(
        default=UNSET, description="Updated gateway public key. Null clears it."
    )
    status: ComputeClusterStatusGQL | None = gql_field(default=UNSET, description="Updated status.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for compute cluster update.",
    ),
    model=UpdateComputeClusterPayloadDTO,
    name="UpdateComputeClusterPayload",
)
class UpdateComputeClusterPayloadGQL(PydanticOutputMixin[UpdateComputeClusterPayloadDTO]):
    compute_cluster: ComputeClusterGQL = gql_field(description="The updated compute cluster.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for compute cluster purge.",
    ),
    model=PurgeComputeClusterPayloadDTO,
    name="PurgeComputeClusterPayload",
)
class PurgeComputeClusterPayloadGQL(PydanticOutputMixin[PurgeComputeClusterPayloadDTO]):
    purged_id: ID = gql_field(description="Global ID of the purged compute cluster.")
    entity_id: UUID = gql_field(description="UUID of the purged compute cluster.")
