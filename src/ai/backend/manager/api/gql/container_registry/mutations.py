"""Container Registry V2 GraphQL mutation input and payload types."""

from __future__ import annotations

from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.container_registry.request import (
    CreateContainerRegistryInput as CreateContainerRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.request import (
    UpdateContainerRegistryInput as UpdateContainerRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    CreateContainerRegistryPayload as CreateContainerRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    DeleteContainerRegistryPayload as DeleteContainerRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    UpdateContainerRegistryPayload as UpdateContainerRegistryPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.container_registry.types import (
    ContainerRegistryGQL,
    ContainerRegistryTypeGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

# ── Inputs ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating a container registry.",
    )
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
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating a container registry. All fields optional except id.",
    )
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


# ── Payloads ──


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for container registry create/update mutations.",
    ),
    model=CreateContainerRegistryPayloadDTO,
)
class CreateContainerRegistryPayloadGQL(PydanticOutputMixin[CreateContainerRegistryPayloadDTO]):
    registry: ContainerRegistryGQL = gql_field(description="The container registry.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for container registry update mutation.",
    ),
    model=UpdateContainerRegistryPayloadDTO,
)
class UpdateContainerRegistryPayloadGQL(PydanticOutputMixin[UpdateContainerRegistryPayloadDTO]):
    registry: ContainerRegistryGQL = gql_field(description="The updated container registry.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for container registry deletion.",
    ),
    model=DeleteContainerRegistryPayloadDTO,
)
class DeleteContainerRegistryPayloadGQL(PydanticOutputMixin[DeleteContainerRegistryPayloadDTO]):
    id: str = gql_field(description="ID of the deleted registry.")
