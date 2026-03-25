"""ProjectV2 GraphQL mutation input and payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.group.request import (
    CreateGroupInput as CreateGroupInputDTO,
)
from ai.backend.common.dto.manager.v2.group.request import (
    UpdateGroupInput as UpdateGroupInputDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    DeleteProjectPayload as DeleteProjectPayloadDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    ProjectPayload as ProjectPayloadDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    PurgeProjectPayload as PurgeProjectPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

UNSET = None


# --- Inputs ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating a new project.",
    )
)
class CreateProjectInputGQL(PydanticInputMixin[CreateGroupInputDTO]):
    """Input for creating a new project."""

    name: str = gql_field(description="Project name. Must be unique within the domain.")
    domain_name: str = gql_field(description="Name of the domain this project belongs to.")
    description: str | None = gql_field(default=UNSET, description="Optional description.")
    integration_id: str | None = gql_field(
        default=UNSET, description="External integration identifier."
    )
    resource_policy: str | None = gql_field(
        default=UNSET, description="Name of the resource policy to apply."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating project information. All fields optional.",
    )
)
class UpdateProjectInputGQL(PydanticInputMixin[UpdateGroupInputDTO]):
    """Input for updating project information."""

    name: str | None = gql_field(default=UNSET, description="New project name.")
    description: str | None = gql_field(default=UNSET, description="New description.")
    is_active: bool | None = gql_field(default=UNSET, description="Updated active status.")
    integration_id: str | None = gql_field(
        default=UNSET, description="New external integration identifier."
    )
    resource_policy: str | None = gql_field(default=UNSET, description="New resource policy name.")


# --- Payloads ---


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for project mutation responses.",
    ),
    model=ProjectPayloadDTO,
)
class ProjectPayloadGQL(PydanticOutputMixin[ProjectPayloadDTO]):
    """Payload for project create/update mutations."""

    project: ProjectV2GQL = gql_field(description="The project entity.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for project deletion mutation.",
    ),
    model=DeleteProjectPayloadDTO,
)
class DeleteProjectPayloadGQL(PydanticOutputMixin[DeleteProjectPayloadDTO]):
    """Payload for project soft-delete."""

    deleted: bool = gql_field(description="Whether the deletion was successful.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for project permanent deletion mutation.",
    ),
    model=PurgeProjectPayloadDTO,
)
class PurgeProjectPayloadGQL(PydanticOutputMixin[PurgeProjectPayloadDTO]):
    """Payload for project permanent purge."""

    purged: bool = gql_field(description="Whether the purge was successful.")
