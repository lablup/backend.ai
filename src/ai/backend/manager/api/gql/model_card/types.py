from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Self
from uuid import UUID

import strawberry
from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    DeploymentRevisionPresetFilter,
    DeploymentRevisionPresetOrder,
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
    DeploymentRevisionPresetOrderField,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    BulkDeleteModelCardsInput as BulkDeleteCardsInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    DeleteModelCardOptions as DeleteOptionsDTO,
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
    ModelCardResourceRequirementFilter as RequirementFilterDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    ModelCardResourceRequirementNestedFilter as RequirementNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    UpdateModelCardInput as UpdateInputDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    BulkDeleteModelCardsPayload as BulkDeleteCardsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    BulkDeleteModelCardV2Error as BulkDeleteModelCardV2ErrorDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    CreateModelCardPayload as CreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    DeleteModelCardPayload as DeletePayloadDTO,
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
    ResourceSlotEntryInfo as ResourceSlotEntryDTO,
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
    ModelCardScope,
    ModelCardUsedBy,
)
from ai.backend.common.dto.manager.v2.model_card.types import (
    ProjectModelCardScope as ProjectModelCardScopeDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter as DateTimeFilterGQL
from ai.backend.manager.api.gql.base import DecimalFilter as DecimalFilterGQL
from ai.backend.manager.api.gql.base import (
    NullableDateTimeFilter as NullableDateTimeFilterGQL,
)
from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.base import UUIDFilter as UUIDFilterGQL
from ai.backend.manager.api.gql.base import UUIDScopeGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.deployment.types.revision_preset import (
    DeploymentRevisionPresetConnection,
    DeploymentRevisionPresetFilterGQL,
    DeploymentRevisionPresetOrderByGQL,
    PresetDeploymentStrategyInputGQL,
)
from ai.backend.manager.api.gql.model_card._preset_helpers import build_preset_connection
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL
    from ai.backend.manager.api.gql.vfolder_v2.types.node import VFolderGQL


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Order fields for model cards.",
    ),
    name="ModelCardV2OrderField",
)
class ModelCardOrderFieldGQL(StrEnum):
    ENTITY_ID = "entity_id"
    NAME = "name"
    VFOLDER_ID = "vfolder_id"
    DOMAIN_NAME = "domain_name"
    PROJECT_ID = "project_id"
    CREATOR_ID = "creator_id"
    AUTHOR = "author"
    TITLE = "title"
    MODEL_VERSION = "model_version"
    TASK = "task"
    CATEGORY = "category"
    ARCHITECTURE = "architecture"
    LICENSE = "license"
    ACCESS_LEVEL = "access_level"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Access level for model cards.",
    ),
    name="ModelCardV2AccessLevel",
)
class ModelCardAccessLevelGQL(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="A single resource requirement entry for a model card. The quantity is represented as a string because model card requirements are descriptive (display/matching) rather than arithmetic.",
    ),
    model=ResourceSlotEntryDTO,
    name="ModelCardV2ResourceSlotEntry",
)
class ModelCardResourceSlotEntryGQL(PydanticOutputMixin[ResourceSlotEntryDTO]):
    resource_type: str = gql_field(
        description="Resource type identifier (e.g., 'cpu', 'mem', 'cuda.shares')."
    )
    quantity: str = gql_field(
        description="Minimum required quantity for this resource as a decimal string."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
        description="Represents a registered AI model with metadata extracted from model-definition.yaml. A model card links to a VFolder containing the actual model files and belongs to a MODEL_STORE type project for access control scoping.",
    ),
    name="ModelCardV2",
)
class ModelCardGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="UUID of the model card.",
        ),
    )
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
    min_resource: list[ModelCardResourceSlotEntryGQL] | None = gql_field(
        description="Minimum resource requirements for serving this model. Each entry maps a resource slot (e.g. 'cpu', 'cuda.shares') to its minimum required quantity. Used to filter compatible deployment revision presets via `available_presets`.",
        default=None,
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

    @gql_field(  # type: ignore[misc]
        description="The VFolder that stores this model card's files. Resolved through a DataLoader so that listing many model cards does not trigger N+1 fetches."
    )
    async def vfolder(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            VFolderGQL,
            strawberry.lazy("ai.backend.manager.api.gql.vfolder_v2.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.vfolder_loader.load(VFolderUUID(self.vfolder_id))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The domain this model card belongs to.",
        )
    )  # type: ignore[misc]
    async def domain(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            DomainV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.domain_v2.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.domain_loader.load(self.domain_name)

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The project this model card belongs to.",
        )
    )  # type: ignore[misc]
    async def project(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            ProjectV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.project_loader.load(ProjectID(self.project_id))

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The user who created this model card.",
        )
    )  # type: ignore[misc]
    async def creator(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.user_loader.load(UserID(self.creator_id))

    @gql_field(  # type: ignore[misc]
        description="Deployment revision presets that satisfy this model card's minimum resource requirements. Equivalent to the root `model_card_available_presets` query but scoped to this card."
    )
    async def available_presets(
        self,
        info: Info[StrawberryGQLContext],
        filter: DeploymentRevisionPresetFilterGQL | None = None,
        order_by: list[DeploymentRevisionPresetOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> DeploymentRevisionPresetConnection | None:
        filter_dto: DeploymentRevisionPresetFilter | None = filter.to_pydantic() if filter else None
        orders_dto: list[DeploymentRevisionPresetOrder] | None = None
        if order_by:
            orders_dto = [
                DeploymentRevisionPresetOrder(
                    field=DeploymentRevisionPresetOrderField(o.field.value),
                    direction=OrderDirection(o.direction),
                )
                for o in order_by
            ]
        search_input = SearchDeploymentRevisionPresetsInput(
            filter=filter_dto,
            order=orders_dto,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        result = await info.context.adapters.model_card.available_presets(
            UUID(self.id), search_input
        )
        return build_preset_connection(result)


ModelCardV2Edge = Edge[ModelCardGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
        description="Scope for model card queries within a MODEL_STORE project.",
    ),
    name="ProjectModelCardV2Scope",
)
class ProjectModelCardScopeGQL(PydanticInputMixin[ProjectModelCardScopeDTO]):
    project_id: UUID = gql_field(description="MODEL_STORE project UUID.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Scope for querying available presets that satisfy a model card's resource requirements.",
    ),
    name="ModelCardAvailablePresetsScope",
)
class ModelCardAvailablePresetsScopeGQL(PydanticInputMixin[AvailablePresetsScopeDTO]):
    model_card_id: UUID = gql_field(
        description="Model card UUID to check resource requirements against."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for one minimum resource requirement of a model card.",
    ),
    name="ModelCardV2ResourceRequirementFilter",
)
class ModelCardResourceRequirementFilterGQL(PydanticInputMixin[RequirementFilterDTO]):
    slot_name: StringFilterGQL | None = gql_field(
        default=None, description="Resource slot name filter."
    )
    min_quantity: DecimalFilterGQL | None = gql_field(
        default=None, description="Minimum quantity filter."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter model cards by conditions on their minimum resource requirements.",
    ),
    name="ModelCardV2ResourceRequirementNestedFilter",
)
class ModelCardResourceRequirementNestedFilterGQL(PydanticInputMixin[RequirementNestedFilterDTO]):
    some: ModelCardResourceRequirementFilterGQL | None = gql_field(
        description="Matches cards with at least one requirement satisfying all conditions.",
        default=None,
    )
    every: ModelCardResourceRequirementFilterGQL | None = gql_field(
        description=(
            "Matches cards where every requirement satisfies all conditions "
            "(also true when the card has none)."
        ),
        default=None,
    )
    none: ModelCardResourceRequirementFilterGQL | None = gql_field(
        description="Matches cards with no requirement satisfying all conditions.",
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version="26.4.2", description="Filter for model cards."),
    name="ModelCardV2Filter",
)
class ModelCardFilterGQL(PydanticInputMixin[FilterDTO]):
    entity_id: UUIDFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="Filter by model card ID."
        ),
        default=None,
    )
    name: StringFilterGQL | None = gql_field(default=None, description="Name filter.")
    vfolder_id: UUIDFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by the VFolder holding the model.",
        ),
        default=None,
    )
    domain_name: StringFilterGQL | None = gql_field(default=None, description="Domain filter.")
    project_id: UUIDFilterGQL | None = gql_field(default=None, description="Project filter.")
    creator_id: UUIDFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by the user who created the model card.",
        ),
        default=None,
    )
    author: StringFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Author filter."),
        default=None,
    )
    title: StringFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Title filter."),
        default=None,
    )
    model_version: StringFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Model version filter."),
        default=None,
    )
    task: StringFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Task filter."),
        default=None,
    )
    category: StringFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Category filter."),
        default=None,
    )
    architecture: StringFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Architecture filter."),
        default=None,
    )
    license: StringFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="License filter."),
        default=None,
    )
    access_level: StringFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "Access level filter. The column stores the level as text, so this is a "
                "string match rather than an enum comparison."
            ),
        ),
        default=None,
    )
    storage_host: StringFilterGQL | None = gql_field(
        default=None,
        description=(
            "Filter by the storage host backing the model card's VFolder. "
            "Matches via an EXISTS subquery against the VFolder host column."
        ),
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. Search vfolders by host first, then "
            "pass their ids as `usedBy.vfolder`."
        ),
    )
    created_at: DateTimeFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="Creation datetime filter."
        ),
        default=None,
    )
    updated_at: NullableDateTimeFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Update datetime filter."),
        default=None,
    )
    min_resource: ModelCardResourceRequirementNestedFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by conditions on the minimum resource requirements.",
        ),
        default=None,
    )
    AND: list[Self] | None = gql_field(
        default=None, description="Combine nested filters with logical AND."
    )
    OR: list[Self] | None = gql_field(
        default=None, description="Combine nested filters with logical OR."
    )
    NOT: list[Self] | None = gql_field(
        default=None, description="Negate the combined result of nested filters."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version="26.4.2", description="Order specification."),
    name="ModelCardV2OrderBy",
)
class ModelCardOrderByGQL(PydanticInputMixin[OrderDTO]):
    field: ModelCardOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version="26.4.2", description="Create model card input."),
    name="CreateModelCardV2Input",
)
class CreateModelCardInputGQL(PydanticInputMixin[CreateInputDTO]):
    name: str = gql_field(description="Model card name.")
    vfolder_id: UUID = gql_field(description="VFolder ID.")
    model_store_project_id: UUID = gql_field(
        description="MODEL_STORE project UUID where the model card belongs."
    )
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
    access_level: ModelCardAccessLevelGQL = gql_field(
        default=ModelCardAccessLevelGQL.INTERNAL,
        description="Access level (public or internal).",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version="26.4.2", description="Update model card input."),
    name="UpdateModelCardV2Input",
)
class UpdateModelCardInputGQL(PydanticInputMixin[UpdateInputDTO]):
    id: UUID = gql_field(description="Model card ID.")
    name: str | None = gql_field(default=UNSET, description="New name.")
    author: str | None = gql_field(default=UNSET, description="Author.")
    title: str | None = gql_field(default=UNSET, description="Title.")
    model_version: str | None = gql_field(default=UNSET, description="Version.")
    description: str | None = gql_field(default=UNSET, description="Description.")
    task: str | None = gql_field(default=UNSET, description="ML task.")
    category: str | None = gql_field(default=UNSET, description="Category.")
    architecture: str | None = gql_field(default=UNSET, description="Architecture.")
    framework: list[str] | None = gql_field(default=UNSET, description="Frameworks.")
    label: list[str] | None = gql_field(default=UNSET, description="Labels.")
    license: str | None = gql_field(default=UNSET, description="License.")
    readme: str | None = gql_field(default=UNSET, description="README content.")
    access_level: ModelCardAccessLevelGQL | None = gql_field(
        default=UNSET, description="Access level (public or internal)."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.4.2", description="Create model card payload."),
    model=CreatePayloadDTO,
    name="CreateModelCardPayload",
)
class CreateModelCardPayloadGQL(PydanticOutputMixin[CreatePayloadDTO]):
    model_card: ModelCardGQL = gql_field(description="The created model card.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.4.2", description="Update model card payload."),
    model=UpdatePayloadDTO,
    name="UpdateModelCardPayload",
)
class UpdateModelCardPayloadGQL(PydanticOutputMixin[UpdatePayloadDTO]):
    model_card: ModelCardGQL = gql_field(description="The updated model card.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.4.2", description="Delete model card payload."),
    model=DeletePayloadDTO,
    name="DeleteModelCardPayload",
)
class DeleteModelCardPayloadGQL(PydanticOutputMixin[DeletePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted model card.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
        description="Input for deploying a model card as a new deployment.",
    ),
    name="DeployModelCardV2Input",
)
class DeployModelCardInputGQL(PydanticInputMixin[DeployInputDTO]):
    project_id: UUID = gql_field(description="Target project UUID for the deployment.")
    revision_preset_id: UUID = gql_field(description="Deployment revision preset UUID.")
    resource_group: str = gql_field(description="Resource group name.")
    desired_replica_count: int = gql_field(default=1, description="Number of replicas.")
    open_to_public: bool | None = gql_field(
        default=None,
        description="Override open_to_public. Defaults to the preset value, then False.",
    )
    replica_count: int | None = gql_field(
        default=None,
        description="Override replica_count. Defaults to the preset value, then desired_replica_count.",
    )
    revision_history_limit: int | None = gql_field(
        default=None,
        description="Override revision_history_limit. Defaults to the preset value, then 10.",
    )
    deployment_strategy: PresetDeploymentStrategyInputGQL | None = gql_field(
        default=None,
        description="Override deployment strategy. Defaults to the preset value, then none.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.4",
        description="Options for the model card delete operation.",
    ),
    name="DeleteModelCardV2Options",
)
class DeleteModelCardOptionsGQL(PydanticInputMixin[DeleteOptionsDTO]):
    """Options for the model card delete operation."""

    delete_associated_vfolder: bool = gql_field(
        description=(
            "If true, also soft-delete (move to trash) the model VFolder(s) "
            "associated with the deleted model card(s)."
        ),
        default=False,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Input for bulk-deleting multiple model cards.",
    ),
    name="BulkDeleteModelCardsV2Input",
)
class BulkDeleteModelCardsV2InputGQL(PydanticInputMixin[BulkDeleteCardsInputDTO]):
    ids: list[UUID] = gql_field(description="List of model card UUIDs to delete.")
    options: DeleteModelCardOptionsGQL | None = gql_field(
        description="Options for the delete operation.",
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Error information for a model card that failed during bulk deletion.",
    ),
    model=BulkDeleteModelCardV2ErrorDTO,
    name="BulkDeleteModelCardV2Error",
)
class BulkDeleteModelCardV2ErrorGQL:
    card_id: UUID = gql_field(description="UUID of the model card that failed to delete.")
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload for bulk model card deletion.",
    ),
    model=BulkDeleteCardsPayloadDTO,
    name="BulkDeleteModelCardsV2Payload",
)
class BulkDeleteModelCardsV2PayloadGQL:
    successes: list[UUID] = gql_field(
        description="UUIDs of model cards that were successfully deleted.",
    )
    failed: list[BulkDeleteModelCardV2ErrorGQL] = gql_field(
        description="List of errors for model cards that failed to delete.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Scope for the scoped model card query. Each list is OR'd internally, and "
            "every scope named is authorized before the read runs."
        ),
    ),
    name="ModelCardScope",
)
class ModelCardScopeGQL(PydanticInputMixin[ModelCardScope]):
    """The scopes a model card read is answered for."""

    domain: list[UUIDScopeGQL] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Domains whose model cards are being read.",
        ),
        default=None,
    )
    project: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Projects whose model cards are being read."
    )
    user: list[UUIDScopeGQL] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Users whose model cards are being read.",
        ),
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Entities whose use narrows a model card query; every id is AND-ed. The caller "
            "must be able to read each listed entity, or the request is refused. Only model "
            "cards the caller can read are returned, even when a listed entity uses others."
        ),
    ),
    name="ModelCardUsedBy",
)
class ModelCardUsedByGQL(PydanticInputMixin[ModelCardUsedBy]):
    """The entities whose use of a model card narrows the read."""

    vfolder: list[UUID] | None = gql_field(
        default=None, description="VFolders the model card is built on."
    )
