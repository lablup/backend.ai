from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    DeleteModelCardsInput as DeleteCardsInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    DeployModelCardInput as DeployInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    ModelCardFilter as FilterDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    ModelCardOrder as OrderDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    UpdateModelCardInput as UpdateInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    CreateModelCardPayload as CreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    DeleteModelCardPayload as DeletePayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    DeleteModelCardsPayload as DeleteCardsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    DeployModelCardPayload as DeployPayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    ModelCardMetadata as ModelCardMetadataDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    ModelCardNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    ScanProjectModelCardsPayload as ScanPayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    UpdateModelCardPayload as UpdatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.types import (
    ModelCardAvailablePresetsScope as AvailablePresetsScopeDTO,
)
from ai.backend.common.dto.manager.v2.model_card.types import (
    ProjectModelCardScope as ProjectModelCardScopeDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Order fields for model cards.",
    ),
    name="ModelCardV2OrderField",
)
class ModelCardOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Access level for model cards.",
    ),
    name="ModelCardV2AccessLevel",
)
class ModelCardAccessLevelGQL(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Metadata extracted from the model-definition.yaml file in the model VFolder. Contains authorship, classification, and framework information used for discovery and compatibility checks.",
    ),
    model=ModelCardMetadataDTO,
    name="ModelCardV2Metadata",
)
class ModelCardMetadataGQL(PydanticOutputMixin[ModelCardMetadataDTO]):
    author: str | None = gql_field(
        description="The author or organization that created this model."
    )
    title: str | None = gql_field(description="Human-readable display title for the model.")
    model_version: str | None = gql_field(
        description="Version string of the model (e.g., '1.0', '2.3.1')."
    )
    description: str | None = gql_field(
        description="Brief summary of what the model does and its intended use cases."
    )
    task: str | None = gql_field(
        description="The primary ML task this model performs (e.g., 'text-generation', 'image-classification')."
    )
    category: str | None = gql_field(
        description="High-level category for the model (e.g., 'NLP', 'Computer Vision')."
    )
    architecture: str | None = gql_field(
        description="Model architecture name (e.g., 'transformer', 'diffusion', 'CNN')."
    )
    framework: list[str] = gql_field(
        description="List of ML frameworks required to run the model (e.g., 'PyTorch', 'TensorFlow', 'JAX')."
    )
    label: list[str] = gql_field(
        description="Classification labels and tags for categorization and search (e.g., 'text-generation', 'vision', 'multilingual')."
    )
    license: str | None = gql_field(
        description="License under which the model is distributed (e.g., 'Apache-2.0', 'MIT')."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Represents a registered AI model with metadata extracted from model-definition.yaml. A model card links to a VFolder containing the actual model files and belongs to a MODEL_STORE type project for access control scoping.",
    ),
    name="ModelCardV2",
)
class ModelCardGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    row_id: UUID = gql_field(description="The unique database identifier of this model card.")
    name: str = gql_field(description="Display name of the registered model.")
    vfolder_id: UUID = gql_field(
        description="The VFolder that stores the actual model files, weights, and configuration."
    )
    domain_name: str = gql_field(
        description="The domain this model card belongs to, used for access control scoping."
    )
    project_id: UUID = gql_field(
        description="The MODEL_STORE type project this model card is associated with for access control."
    )
    creator_id: UUID = gql_field(description="The user who registered this model card.")
    metadata: ModelCardMetadataGQL = gql_field(
        description="Model metadata including authorship, classification, framework info, and licensing extracted from model-definition.yaml."
    )
    readme: str | None = gql_field(
        description="README content from the model VFolder, typically containing usage instructions and model documentation."
    )
    access_level: ModelCardAccessLevelGQL = gql_field(
        description="Access level of the model card (public or internal)."
    )
    created_at: datetime = gql_field(description="Timestamp when this model card was registered.")
    updated_at: datetime | None = gql_field(
        description="Timestamp of the last modification to this model card."
    )


ModelCardV2Edge = Edge[ModelCardGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated list of model cards.",
    )
)
class ModelCardV2Connection(Connection[ModelCardGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Scope for model card queries within a MODEL_STORE project.",
    ),
    name="ProjectModelCardV2Scope",
)
class ProjectModelCardScopeGQL(PydanticInputMixin[ProjectModelCardScopeDTO]):
    project_id: UUID = gql_field(description="MODEL_STORE project UUID.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Scope for querying available presets that satisfy a model card's resource requirements.",
    ),
    name="ModelCardAvailablePresetsV2Scope",
)
class ModelCardAvailablePresetsScopeGQL(PydanticInputMixin[AvailablePresetsScopeDTO]):
    model_card_id: UUID = gql_field(
        description="Model card UUID to check resource requirements against."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Filter for model cards."),
    name="ModelCardV2Filter",
)
class ModelCardFilterGQL(PydanticInputMixin[FilterDTO]):
    name: StringFilterGQL | None = gql_field(default=None, description="Name filter.")
    domain_name: str | None = gql_field(default=None, description="Domain filter.")
    project_id: UUID | None = gql_field(default=None, description="Project filter.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Order specification."),
    name="ModelCardV2OrderBy",
)
class ModelCardOrderByGQL(PydanticInputMixin[OrderDTO]):
    field: ModelCardOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Create model card input."),
    name="CreateModelCardV2Input",
)
class CreateModelCardInputGQL(PydanticInputMixin[CreateInputDTO]):
    name: str = gql_field(description="Model card name.")
    vfolder_id: UUID = gql_field(description="VFolder ID.")
    project_id: UUID = gql_field(description="Project ID.")
    domain_name: str | None = gql_field(default=None, description="Domain name.")
    author: str | None = gql_field(default=None, description="Author.")
    title: str | None = gql_field(default=None, description="Model title.")
    model_version: str | None = gql_field(default=None, description="Model version.")
    description: str | None = gql_field(default=None, description="Description.")
    task: str | None = gql_field(default=None, description="ML task.")
    category: str | None = gql_field(default=None, description="Category.")
    architecture: str | None = gql_field(default=None, description="Architecture.")
    framework: list[str] | None = gql_field(default=None, description="Frameworks.")
    label: list[str] | None = gql_field(default=None, description="Labels.")
    license: str | None = gql_field(default=None, description="License.")
    readme: str | None = gql_field(default=None, description="README content.")
    access_level: ModelCardAccessLevelGQL | None = gql_field(
        default=None, description="Access level (public or internal)."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Update model card input."),
    name="UpdateModelCardV2Input",
)
class UpdateModelCardInputGQL(PydanticInputMixin[UpdateInputDTO]):
    id: UUID = gql_field(description="Model card ID.")
    name: str | None = gql_field(default=None, description="New name.")
    author: str | None = gql_field(default=None, description="Author.")
    title: str | None = gql_field(default=None, description="Title.")
    model_version: str | None = gql_field(default=None, description="Version.")
    description: str | None = gql_field(default=None, description="Description.")
    task: str | None = gql_field(default=None, description="ML task.")
    category: str | None = gql_field(default=None, description="Category.")
    architecture: str | None = gql_field(default=None, description="Architecture.")
    framework: list[str] | None = gql_field(default=None, description="Frameworks.")
    label: list[str] | None = gql_field(default=None, description="Labels.")
    license: str | None = gql_field(default=None, description="License.")
    readme: str | None = gql_field(default=None, description="README content.")
    access_level: ModelCardAccessLevelGQL | None = gql_field(
        default=None, description="Access level (public or internal)."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Create model card payload."),
    model=CreatePayloadDTO,
)
class CreateModelCardPayloadGQL(PydanticOutputMixin[CreatePayloadDTO]):
    model_card: ModelCardGQL = gql_field(description="The created model card.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Update model card payload."),
    model=UpdatePayloadDTO,
)
class UpdateModelCardPayloadGQL(PydanticOutputMixin[UpdatePayloadDTO]):
    model_card: ModelCardGQL = gql_field(description="The updated model card.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Delete model card payload."),
    model=DeletePayloadDTO,
)
class DeleteModelCardPayloadGQL(PydanticOutputMixin[DeletePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted model card.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Result of scanning a MODEL_STORE project for model cards.",
    ),
    model=ScanPayloadDTO,
    name="ScanProjectModelCardsV2Payload",
)
class ScanProjectModelCardsPayloadGQL(PydanticOutputMixin[ScanPayloadDTO]):
    created_count: int = gql_field(description="Number of newly created model cards.")
    updated_count: int = gql_field(description="Number of updated model cards.")
    errors: list[str] = gql_field(description="Per-vfolder error messages.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for deploying a model card as a new deployment.",
    ),
    name="DeployModelCardV2Input",
)
class DeployModelCardInputGQL(PydanticInputMixin[DeployInputDTO]):
    project_id: UUID = gql_field(description="Target project UUID for the deployment.")
    revision_preset_id: UUID = gql_field(description="Deployment revision preset UUID.")
    resource_group: str = gql_field(description="Resource group name.")
    desired_replica_count: int = gql_field(default=1, description="Number of replicas.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Result of deploying a model card.",
    ),
    model=DeployPayloadDTO,
    name="DeployModelCardV2Payload",
)
class DeployModelCardPayloadGQL(PydanticOutputMixin[DeployPayloadDTO]):
    deployment_id: UUID = gql_field(description="ID of the created deployment.")
    deployment_name: str = gql_field(description="Name of the created deployment.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for deleting multiple model cards.",
    ),
    name="DeleteModelCardsV2Input",
)
class DeleteModelCardsInputGQL(PydanticInputMixin[DeleteCardsInputDTO]):
    ids: list[UUID] = gql_field(description="List of model card UUIDs to delete.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for bulk model card deletion.",
    ),
    model=DeleteCardsPayloadDTO,
    name="DeleteModelCardsV2Payload",
)
class DeleteModelCardsPayloadGQL(PydanticOutputMixin[DeleteCardsPayloadDTO]):
    deleted_count: int = gql_field(description="Number of model cards successfully deleted.")
