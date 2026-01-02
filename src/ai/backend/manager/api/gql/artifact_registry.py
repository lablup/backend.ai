from __future__ import annotations

from typing import Optional

import strawberry
from strawberry import ID, Info

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.artifact.types import (
    ArtifactType,
)
from ai.backend.manager.errors.api import NotImplementedAPI
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
)


@strawberry.type(description="Added in 25.14.0")
class ArtifactRegistry:
    id: ID = strawberry.field(
        description=(
            "Added in 25.17.0. "
            "Internal identifier for the artifact registry metadata record in the 'artifact_registries' table. "
            "This ID is unique across all registry types and represents the metadata record itself. "
            "Example: When you need to reference a registry entry in the metadata table, use this ID."
        )
    )
    registry_id: ID = strawberry.field(
        description=(
            "Added in 25.17.0. "
            "Identifier of the actual registry implementation (e.g., HuggingFace registry, Reservoir registry). "
            "This ID corresponds to the primary key in the registry-type-specific table. "
            "Example: For a HuggingFace registry, this value matches the 'id' field in the 'huggingface_registries' table. "
            "Use this ID when you need to access type-specific registry details."
        )
    )
    name: str = strawberry.field(description="Name of the default artifact registry.")
    type: ArtifactRegistryType = strawberry.field(
        description="Type of the default artifact registry."
    )


@strawberry.field(description="Added in 25.14.0")
async def default_artifact_registry(
    artifact_type: ArtifactType, info: Info[StrawberryGQLContext]
) -> Optional[ArtifactRegistry]:
    artifact_registry_cfg = info.context.config_provider.config.artifact_registry
    if artifact_registry_cfg is None:
        raise ServerMisconfiguredError("Artifact registry configuration is missing.")

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

    registry_data = artifact_registry_meta.result

    return ArtifactRegistry(
        id=ID(str(registry_data.id)),
        registry_id=ID(str(registry_data.registry_id)),
        name=registry_name,
        type=registry_data.type,
    )
