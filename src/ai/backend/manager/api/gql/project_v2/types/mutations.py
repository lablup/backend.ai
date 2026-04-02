"""ProjectV2 GraphQL mutation input and payload types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.group.request import (
    CreateProjectInput as CreateProjectInputDTO,
)
from ai.backend.common.dto.manager.v2.group.request import (
    UnassignUsersFromProjectInput as UnassignUsersFromProjectInputDTO,
)
from ai.backend.common.dto.manager.v2.group.request import (
    UpdateProjectInput as UpdateProjectInputDTO,
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
from ai.backend.common.dto.manager.v2.group.response import (
    UnassignUserError as UnassignUserErrorDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    UnassignUsersFromProjectPayload as UnassignUsersFromProjectPayloadDTO,
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
from ai.backend.manager.api.gql.user.types.node import UserV2GQL

UNSET = None


# --- Inputs ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating a new project.",
    )
)
class CreateProjectInputGQL(PydanticInputMixin[CreateProjectInputDTO]):
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
class UpdateProjectInputGQL(PydanticInputMixin[UpdateProjectInputDTO]):
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


# --- Unassign Users ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for unassigning users from a project.",
    ),
    name="UnassignUsersFromProjectInput",
)
class UnassignUsersFromProjectInputGQL(PydanticInputMixin[UnassignUsersFromProjectInputDTO]):
    """Input for unassigning users from a project."""

    user_ids: list[UUID] = gql_field(description="List of user UUIDs to unassign from the project.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Error information for a user that failed to be unassigned.",
    ),
    model=UnassignUserErrorDTO,
    name="UnassignUserError",
)
class UnassignUserErrorGQL(PydanticOutputMixin[UnassignUserErrorDTO]):
    """Error information for a user that failed to be unassigned."""

    user_id: UUID = gql_field(description="UUID of the user that failed to be unassigned.")
    message: str = gql_field(description="Error message describing the failure reason.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for user unassignment from project.",
    ),
    model=UnassignUsersFromProjectPayloadDTO,
    name="UnassignUsersFromProjectPayload",
)
class UnassignUsersFromProjectPayloadGQL(PydanticOutputMixin[UnassignUsersFromProjectPayloadDTO]):
    """Payload for user unassignment from project."""

    unassigned_users: list[UserV2GQL] = gql_field(
        description="List of users that were unassigned from the project.",
    )
    failed: list[UnassignUserErrorGQL] = gql_field(
        description="List of errors for users that could not be unassigned.",
    )
