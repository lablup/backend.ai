from __future__ import annotations

from typing import Optional

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.artifact.types import (
    ArtifactType,
)


@strawberry.type(description="Added in 25.14.0")
class DefaultArtifactRegistry:
    name: str = strawberry.field(description="Name of the default artifact registry.")


@strawberry.field(description="Added in 25.14.0")
async def default_artifact_registry(
    artifact_type: ArtifactType, info: Info[StrawberryGQLContext]
) -> Optional[DefaultArtifactRegistry]:
    artifact_registry_cfg = info.context.config_provider.config.artifact_registry

    match artifact_type:
        case ArtifactType.MODEL:
            return DefaultArtifactRegistry(name=artifact_registry_cfg.model_registry)
        case _:
            raise NotImplementedError(
                f"Default registry for artifact type {artifact_type} is not implemented."
            )
