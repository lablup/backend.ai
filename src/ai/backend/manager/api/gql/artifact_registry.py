from __future__ import annotations

from typing import Optional

import strawberry
from strawberry import Info

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.artifact.types import (
    ArtifactType,
)
from ai.backend.manager.errors.api import NotImplementedAPI
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
)


@strawberry.type(description="Added in 25.14.0")
class ArtifactRegistry:
    name: str = strawberry.field(description="Name of the default artifact registry.")
    type: ArtifactRegistryType = strawberry.field(
        description="Type of the default artifact registry."
    )


@strawberry.field(description="Added in 25.14.0")
async def default_artifact_registry(
    artifact_type: ArtifactType, info: Info[StrawberryGQLContext]
) -> Optional[ArtifactRegistry]:
    artifact_registry_cfg = info.context.config_provider.config.artifact_registry

    registry_name: Optional[str] = None
    match artifact_type:
        case ArtifactType.MODEL:
            registry_name = artifact_registry_cfg.model_registry
        case _:
            raise NotImplementedAPI(
                f"Default registry for artifact type {artifact_type} is not implemented."
            )

    artifact_registry_meta = (
        await info.context.processors.artifact_registry.get_registry_meta.wait_for_complete(
            GetArtifactRegistryMetaAction(registry_name=registry_name)
        )
    )

    registry_type = artifact_registry_meta.result.type

    return ArtifactRegistry(
        name=registry_name,
        type=registry_type,
    )
