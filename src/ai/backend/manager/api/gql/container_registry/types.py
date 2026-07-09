"""GraphQL types for container registry."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Self, cast, override
from uuid import UUID

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.image.request import AdminSearchImagesInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.image.types import (
    ImageV2ConnectionGQL,
    ImageV2EdgeGQL,
    ImageV2FilterGQL,
    ImageV2GQL,
    ImageV2OrderByGQL,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.image.conditions import ImageConditions


@gql_enum(
    BackendAIGQLMeta(added_version="26.4.0", description="Container registry type."),
    name="ContainerRegistryType",
)
class ContainerRegistryTypeGQL(StrEnum):
    DOCKER = "docker"
    HARBOR = "harbor"
    HARBOR2 = "harbor2"
    GITHUB = "github"
    GITLAB = "gitlab"
    ECR = "ecr"
    ECR_PUB = "ecr-public"
    LOCAL = "local"
    OCP = "ocp"


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.4.0",
        description="Container registry node.",
    ),
    name="ContainerRegistryV2",
)
class ContainerRegistryGQL(PydanticNodeMixin[Any]):
    id: NodeID[str] = gql_field(
        description="Relay-style global node identifier for the container registry"
    )
    url: str = gql_field(description="URL of the container registry")
    registry_name: str = gql_field(description="Name of the container registry")
    type: ContainerRegistryTypeGQL = gql_field(description="Type of the container registry")
    project: str | None = gql_field(
        description="Project or namespace within the registry", default=None
    )
    username: str | None = gql_field(
        description="Username for registry authentication", default=None
    )
    password: str | None = gql_field(
        description="Masked password for registry authentication", default=None
    )
    ssl_verify: bool | None = gql_field(
        description="Whether SSL verification is enabled", default=None
    )
    is_global: bool | None = gql_field(
        description="Whether this registry is globally accessible", default=None
    )
    extra: JSON | None = gql_field(
        description="Extra metadata for the container registry", default=None
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Container images stored in this registry. Returns a paginated connection scoped to this registry, so the registry->images relationship can be traversed directly on the node instead of a separate containerRegistryImagesV2 query.",
        )
    )  # type: ignore[misc]
    async def images(
        self,
        info: Info[StrawberryGQLContext],
        filter: ImageV2FilterGQL | None = None,
        order_by: list[ImageV2OrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ImageV2ConnectionGQL | None:
        base_conditions = [ImageConditions.by_registry_id(UUID(self.id))]
        payload = await info.context.adapters.image.admin_search_images_gql(
            AdminSearchImagesInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
            base_conditions=base_conditions,
        )
        edges = [
            ImageV2EdgeGQL(
                node=ImageV2GQL.from_pydantic(node),
                cursor=encode_cursor(node.id),
            )
            for node in payload.items
        ]
        page_info = PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )
        return ImageV2ConnectionGQL(count=payload.total_count, edges=edges, page_info=page_info)

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.container_registry_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


ContainerRegistryV2Edge = Edge[ContainerRegistryGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Paginated connection for container registries.",
    )
)
class ContainerRegistryV2Connection(Connection[ContainerRegistryGQL]):
    count: int = gql_field(description="Total number of matching registries.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
