"""GraphQL types for container registry."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Self
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Node, NodeID
from strawberry.scalars import JSON

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER


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

    @classmethod
    def from_enum(cls, value: ContainerRegistryType) -> ContainerRegistryTypeGQL:
        return cls(value.value)


@strawberry.type(
    name="ContainerRegistryV2",
    description="Added in 26.4.0. Container registry node.",
)
class ContainerRegistryGQL(Node):
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
        return [cls.from_data(data) if data is not None else None for data in results]

    @classmethod
    def from_data(cls, data: ContainerRegistryData) -> Self:
        return cls(
            id=str(data.id),
            url=data.url,
            registry_name=data.registry_name,
            type=ContainerRegistryTypeGQL.from_enum(data.type),
            project=data.project,
            username=data.username,
            password=PASSWORD_PLACEHOLDER if data.password is not None else None,
            ssl_verify=data.ssl_verify,
            is_global=data.is_global,
            extra=data.extra,
        )
