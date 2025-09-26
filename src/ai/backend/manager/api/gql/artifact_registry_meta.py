from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Self

import strawberry
from aiotools import apartial
from strawberry import ID
from strawberry.dataloader import DataLoader
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryData,
)
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
)

from .types import StrawberryGQLContext


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Represents common metadata for an artifact registry.
    All artifact registry nodes expose that information regardless of type.
""")
)
class ArtifactRegistryMeta(Node):
    id: NodeID[str]
    name: str
    registry_id: ID
    type: ArtifactRegistryType
    url: str

    @classmethod
    def from_dataclass(cls, data: ArtifactRegistryData, url: str) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            registry_id=ID(str(data.registry_id)),
            type=data.type,
            url=url,
        )

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, registry_ids: Sequence[uuid.UUID]
    ) -> list[Self]:
        from ai.backend.manager.api.gql.huggingface_registry import HuggingFaceRegistry
        from ai.backend.manager.api.gql.reservoir_registry import ReservoirRegistry

        # Get all registry metas in a single batch query
        registry_metas_action = (
            await ctx.processors.artifact_registry.get_registry_metas.wait_for_complete(
                GetArtifactRegistryMetasAction(registry_ids=list(registry_ids))
            )
        )

        # Create a mapping for efficient lookup
        registry_meta_map = {meta.registry_id: meta for meta in registry_metas_action.result}

        registries = []
        for registry_id in registry_ids:
            if registry_id not in registry_meta_map:
                raise ArtifactRegistryNotFoundError

            registry_meta = registry_meta_map[registry_id]
            registry_type = registry_meta.type
            url = None

            match registry_type:
                case ArtifactRegistryType.HUGGINGFACE:
                    registry_meta_loader = DataLoader(
                        apartial(HuggingFaceRegistry.load_by_id, ctx),
                    )
                    hf_registry = await registry_meta_loader.load(registry_id)
                    url = hf_registry.url
                case ArtifactRegistryType.RESERVOIR:
                    registry_meta_loader = DataLoader(
                        apartial(ReservoirRegistry.load_by_id, ctx),
                    )
                    reservoir_registry = await registry_meta_loader.load(registry_id)
                    url = reservoir_registry.endpoint

            registries.append(cls.from_dataclass(registry_meta, url=url))
        return registries


ArtifactRegistryMetaEdge = Edge[ArtifactRegistryMeta]


@strawberry.type(description="Added in 25.15.0")
class ArtifactRegistryMetaConnection(Connection[ArtifactRegistryMeta]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count
