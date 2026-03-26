from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, Self

from strawberry import ID
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError

from .types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Represents common metadata for an artifact registry. All artifact registry nodes expose that information regardless of type.",
    ),
)
class ArtifactRegistryMeta(PydanticNodeMixin[Any]):
    id: NodeID[str]
    name: str
    registry_id: ID
    type: ArtifactRegistryType
    url: str

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, registry_ids: Sequence[uuid.UUID]
    ) -> list[Self]:
        # Get all registry metas in a single batch query
        registry_meta_dtos = await ctx.adapters.artifact_registry.get_registry_metas(
            list(registry_ids)
        )

        # Create a mapping for efficient lookup
        registry_meta_map = {meta.registry_id: meta for meta in registry_meta_dtos}

        registries = []
        for registry_id in registry_ids:
            if registry_id not in registry_meta_map:
                raise ArtifactRegistryNotFoundError

            registry_meta = registry_meta_map[registry_id]
            registry_type = registry_meta.type
            url: str | None = None

            match registry_type:
                case ArtifactRegistryType.HUGGINGFACE:
                    hf_registry = await ctx.data_loaders.huggingface_registry_loader.load(
                        registry_id
                    )
                    if hf_registry is None:
                        raise ArtifactRegistryNotFoundError
                    url = hf_registry.url
                case ArtifactRegistryType.RESERVOIR:
                    reservoir_registry = await ctx.data_loaders.reservoir_registry_loader.load(
                        registry_id
                    )
                    if reservoir_registry is None:
                        raise ArtifactRegistryNotFoundError
                    url = reservoir_registry.endpoint

            registries.append(
                cls(
                    id=ID(str(registry_meta.id)),
                    name=registry_meta.name,
                    registry_id=ID(str(registry_meta.registry_id)),
                    type=registry_meta.type,
                    url=url,
                )
            )
        return registries


ArtifactRegistryMetaEdge = Edge[ArtifactRegistryMeta]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Relay-style connection for paginated artifact registry meta queries.",
    ),
)
class ArtifactRegistryMetaConnection(Connection[ArtifactRegistryMeta]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
