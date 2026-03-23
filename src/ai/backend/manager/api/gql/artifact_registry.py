from __future__ import annotations

from strawberry import ID, Info

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.dto.manager.v2.artifact_registry.response import (
    ArtifactRegistryGQLNode,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_field,
    gql_pydantic_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.artifact.types import (
    ArtifactType,
)
from ai.backend.manager.errors.api import NotImplementedAPI
from ai.backend.manager.errors.common import ServerMisconfiguredError


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Artifact registry node.",
    ),
    model=ArtifactRegistryGQLNode,
)
class ArtifactRegistry:
    id: ID = gql_added_field(
        BackendAIGQLMeta(
            added_version="25.17.0",
            description="Internal identifier for the artifact registry metadata record in the 'artifact_registries' table. This ID is unique across all registry types and represents the metadata record itself. Example: When you need to reference a registry entry in the metadata table, use this ID.",
        )
    )
    registry_id: ID = gql_added_field(
        BackendAIGQLMeta(
            added_version="25.17.0",
            description="Identifier of the actual registry implementation (e.g., HuggingFace registry, Reservoir registry). This ID corresponds to the primary key in the registry-type-specific table. Example: For a HuggingFace registry, this value matches the 'id' field in the 'huggingface_registries' table. Use this ID when you need to access type-specific registry details.",
        )
    )
    name: str = gql_field(description="Name of the default artifact registry.")
    type: ArtifactRegistryType = gql_field(description="Type of the default artifact registry.")


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Get the default artifact registry for a given artifact type",
    )
)  # type: ignore[misc]
async def default_artifact_registry(
    artifact_type: ArtifactType, info: Info[StrawberryGQLContext]
) -> ArtifactRegistry | None:
    artifact_registry_cfg = info.context.config_provider.config.artifact_registry
    if artifact_registry_cfg is None:
        raise ServerMisconfiguredError("Artifact registry configuration is missing.")

    registry_name: str | None = None
    match artifact_type:
        case ArtifactType.MODEL:
            registry_name = artifact_registry_cfg.model_registry
        case _:
            raise NotImplementedAPI(
                f"Default registry for artifact type {artifact_type} is not implemented."
            )

    registry_data = await info.context.adapters.artifact_registry.get_registry_meta(
        registry_name=registry_name
    )

    return ArtifactRegistry(
        id=ID(str(registry_data.id)),
        registry_id=ID(str(registry_data.registry_id)),
        name=registry_name,
        type=registry_data.type,
    )
