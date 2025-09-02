from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Self

import strawberry
from aiotools import apartial
from strawberry import ID
from strawberry.dataloader import DataLoader
from strawberry.relay import Node, NodeID

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.api.gql.huggingface_registry import HuggingFaceRegistry
from ai.backend.manager.api.gql.reservoir_registry import ReservoirRegistry
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryData,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
)

from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.13.0")
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
        registries = []

        for registry_id in registry_ids:
            action_result = (
                await ctx.processors.artifact_registry.get_registry_meta.wait_for_complete(
                    GetArtifactRegistryMetaAction(registry_id=registry_id)
                )
            )

            registry_type = action_result.result.type
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

            registries.append(cls.from_dataclass(action_result.result, url=url))
        return registries
