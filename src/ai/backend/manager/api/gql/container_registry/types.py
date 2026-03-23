"""GraphQL types for container registry."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import NodeID
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_node_type
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.enum(
    name="ContainerRegistryType", description="Added in 26.4.0. Container registry type."
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
    id: NodeID[str] = strawberry.field(
        description="Relay-style global node identifier for the container registry"
    )
    url: str = strawberry.field(description="URL of the container registry")
    registry_name: str = strawberry.field(description="Name of the container registry")
    type: ContainerRegistryTypeGQL = strawberry.field(description="Type of the container registry")
    project: str | None = strawberry.field(
        description="Project or namespace within the registry", default=None
    )
    username: str | None = strawberry.field(
        description="Username for registry authentication", default=None
    )
    password: str | None = strawberry.field(
        description="Masked password for registry authentication", default=None
    )
    ssl_verify: bool | None = strawberry.field(
        description="Whether SSL verification is enabled", default=None
    )
    is_global: bool | None = strawberry.field(
        description="Whether this registry is globally accessible", default=None
    )
    extra: JSON | None = strawberry.field(
        description="Extra metadata for the container registry", default=None
    )

    @classmethod
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
