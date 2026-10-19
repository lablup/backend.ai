"""Container Registry V2 GraphQL mutation input and payload types."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.container_registry.request import (
    CreateContainerRegistryInput as CreateContainerRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.request import (
    PartialBulkPurgeContainerRegistriesInput as PartialBulkPurgeContainerRegistriesInputDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.request import (
    UpdateContainerRegistryInput as UpdateContainerRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    ContainerRegistryNode,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    CreateContainerRegistryPayload as CreateContainerRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    DeleteContainerRegistryPayload as DeleteContainerRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    PurgeContainerRegistryPayload as PurgeContainerRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    UpdateContainerRegistryPayload as UpdateContainerRegistryPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import PartialBulkFailureGQL
from ai.backend.manager.api.gql.container_registry.types import (
    ContainerRegistryGQL,
    ContainerRegistryTypeGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

# ── Inputs ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for creating a container registry.",
    ),
    name="CreateContainerRegistryInputV2",
)
class CreateContainerRegistryInputGQL(PydanticInputMixin[CreateContainerRegistryInputDTO]):
    url: str = gql_field(description="URL of the container registry.")
    registry_name: str = gql_field(description="Unique name of the container registry.")
    type: ContainerRegistryTypeGQL = gql_field(description="Type of the container registry.")
    project: str | None = gql_field(default=None, description="Project or namespace.")
    username: str | None = gql_field(default=None, description="Username for authentication.")
    password: str | None = gql_field(default=None, description="Password for authentication.")
    ssl_verify: bool | None = gql_field(default=None, description="Whether to verify SSL.")
    is_global: bool | None = gql_field(default=None, description="Whether globally accessible.")
    extra: JSON | None = gql_field(default=None, description="Extra metadata.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for updating a container registry. All fields optional except id.",
    ),
    name="UpdateContainerRegistryInput",
)
class UpdateContainerRegistryInputGQL(PydanticInputMixin[UpdateContainerRegistryInputDTO]):
    id: str = gql_field(description="ID of the registry to update.")
    url: str | None = gql_field(default=None, description="Updated URL.")
    registry_name: str | None = gql_field(default=None, description="Updated registry name.")
    type: ContainerRegistryTypeGQL | None = gql_field(default=None, description="Updated type.")
    project: str | None = gql_field(default=None, description="Updated project.")
    username: str | None = gql_field(default=None, description="Updated username.")
    password: str | None = gql_field(default=None, description="Updated password.")
    ssl_verify: bool | None = gql_field(default=None, description="Updated SSL verification.")
    is_global: bool | None = gql_field(default=None, description="Updated global accessibility.")
    extra: JSON | None = gql_field(default=None, description="Updated extra metadata.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for purging several container registries, each answered for separately.",
    ),
    name="PartialBulkPurgeContainerRegistriesInput",
)
class PartialBulkPurgeContainerRegistriesInputGQL(
    PydanticInputMixin[PartialBulkPurgeContainerRegistriesInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the container registries to purge.")


# ── Payloads ──


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for container registry create/update mutations.",
    ),
    model=CreateContainerRegistryPayloadDTO,
    name="CreateContainerRegistryPayload",
)
class CreateContainerRegistryPayloadGQL(PydanticOutputMixin[CreateContainerRegistryPayloadDTO]):
    registry: ContainerRegistryGQL = gql_field(description="The container registry.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for container registry update mutation.",
    ),
    model=UpdateContainerRegistryPayloadDTO,
    name="UpdateContainerRegistryPayload",
)
class UpdateContainerRegistryPayloadGQL(PydanticOutputMixin[UpdateContainerRegistryPayloadDTO]):
    registry: ContainerRegistryGQL = gql_field(description="The updated container registry.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for container registry deletion.",
    ),
    model=DeleteContainerRegistryPayloadDTO,
    name="DeleteContainerRegistryPayload",
)
class DeleteContainerRegistryPayloadGQL(PydanticOutputMixin[DeleteContainerRegistryPayloadDTO]):
    id: str = gql_field(description="ID of the deleted registry.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for container registry purge.",
    ),
    model=PurgeContainerRegistryPayloadDTO,
    name="PurgeContainerRegistryPayload",
)
class PurgeContainerRegistryPayloadGQL(PydanticOutputMixin[PurgeContainerRegistryPayloadDTO]):
    id: UUID = gql_field(
        description="ID of the purged registry.",
        deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgedId` or `entityId`.",
    )
    purged_id: strawberry.ID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Global ID of the purged container registry.",
        ),
    )
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="UUID of the purged container registry."
        ),
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk container registry operation: the registries processed "
            "and the ones that failed."
        ),
    ),
    model=PartialBulkPayload[ContainerRegistryNode],
    name="PartialBulkContainerRegistriesPayload",
)
class PartialBulkContainerRegistriesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[ContainerRegistryNode]]
):
    """Payload for partial bulk container registry mutations."""

    successes: list[ContainerRegistryGQL] = gql_field(
        description="The container registries processed, as they stood."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The container registries not processed, each with the reason."
    )
