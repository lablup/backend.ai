"""ProjectV2 GraphQL mutation input and payload types."""

from __future__ import annotations

from uuid import UUID

from strawberry import UNSET

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.group.request import (
    CreateProjectInput as CreateProjectInputDTO,
)
from ai.backend.common.dto.manager.v2.group.request import (
    PartialBulkDeleteProjectsInput as PartialBulkDeleteProjectsInputDTO,
)
from ai.backend.common.dto.manager.v2.group.request import (
    PartialBulkRestoreProjectsInput as PartialBulkRestoreProjectsInputDTO,
)
from ai.backend.common.dto.manager.v2.group.request import (
    PartialBulkUpdateProjectItemInput as PartialBulkUpdateProjectItemInputDTO,
)
from ai.backend.common.dto.manager.v2.group.request import (
    PartialBulkUpdateProjectsInput as PartialBulkUpdateProjectsInputDTO,
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
    ProjectNode,
)
from ai.backend.common.dto.manager.v2.group.response import (
    ProjectPayload as ProjectPayloadDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    PurgeProjectPayload as PurgeProjectPayloadDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    RestoreProjectPayload as RestoreProjectPayloadDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    UnassignUserError as UnassignUserErrorDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    UnassignUsersFromProjectPayload as UnassignUsersFromProjectPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import PartialBulkFailureGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.user.types.node import UserV2GQL

# --- Inputs ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for creating a new project.",
    ),
    name="CreateProjectInput",
)
class CreateProjectInputGQL(PydanticInputMixin[CreateProjectInputDTO]):
    """Input for creating a new project."""

    name: str = gql_field(description="Project name. Must be unique within the domain.")
    domain_name: str = gql_field(description="Name of the domain this project belongs to.")
    description: str | None = gql_field(default=None, description="Optional description.")
    integration_name: str | None = gql_field(
        default=None, description="External integration identifier."
    )
    resource_policy: str | None = gql_field(
        default=None, description="Name of the resource policy to apply."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for updating project information. All fields optional.",
    ),
    name="UpdateProjectInput",
)
class UpdateProjectInputGQL(PydanticInputMixin[UpdateProjectInputDTO]):
    """Input for updating project information."""

    name: str | None = gql_field(default=UNSET, description="New project name.")
    description: str | None = gql_field(default=UNSET, description="New description.")
    is_active: bool | None = gql_field(
        default=UNSET,
        description=(
            "`false` runs `deleteProjectV2` and `true` runs `restoreProjectV2`; nothing happens "
            "when the project is already in that state."
        ),
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. Use `deleteProjectV2` or `restoreProjectV2`."
        ),
    )
    integration_name: str | None = gql_field(
        default=UNSET, description="New external integration identifier."
    )
    resource_policy: str | None = gql_field(default=UNSET, description="New resource policy name.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One project of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateProjectItemInput",
)
class PartialBulkUpdateProjectItemInputGQL(
    PydanticInputMixin[PartialBulkUpdateProjectItemInputDTO]
):
    id: UUID = gql_field(description="ID of the project to update.")
    input: UpdateProjectInputGQL = gql_field(description="Fields to update on the project.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating several projects, each answered for separately.",
    ),
    name="PartialBulkUpdateProjectsInput",
)
class PartialBulkUpdateProjectsInputGQL(PydanticInputMixin[PartialBulkUpdateProjectsInputDTO]):
    items: list[PartialBulkUpdateProjectItemInputGQL] = gql_field(
        description="The projects to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for soft-deleting several projects, each answered for separately.",
    ),
    name="PartialBulkDeleteProjectsInput",
)
class PartialBulkDeleteProjectsInputGQL(PydanticInputMixin[PartialBulkDeleteProjectsInputDTO]):
    ids: list[UUID] = gql_field(description="IDs of the projects to soft-delete.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for restoring several soft-deleted projects, each answered for separately."
        ),
    ),
    name="PartialBulkRestoreProjectsInput",
)
class PartialBulkRestoreProjectsInputGQL(PydanticInputMixin[PartialBulkRestoreProjectsInputDTO]):
    ids: list[UUID] = gql_field(description="IDs of the projects to restore.")


# --- Payloads ---


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for project mutation responses.",
    ),
    model=ProjectPayloadDTO,
    name="ProjectPayload",
)
class ProjectPayloadGQL(PydanticOutputMixin[ProjectPayloadDTO]):
    """Payload for project create/update mutations."""

    project: ProjectV2GQL = gql_field(description="The project entity.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for project deletion mutation.",
    ),
    model=DeleteProjectPayloadDTO,
    name="DeleteProjectPayload",
)
class DeleteProjectPayloadGQL(PydanticOutputMixin[DeleteProjectPayloadDTO]):
    """Payload for project soft-delete."""

    deleted: bool = gql_field(
        description="Whether the deletion was successful.",
        deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `project`.",
    )
    project: ProjectV2GQL = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="The soft-deleted project."
        ),
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.9.0",
        description="Payload for project restore mutation.",
    ),
    model=RestoreProjectPayloadDTO,
    name="RestoreProjectPayload",
)
class RestoreProjectPayloadGQL(PydanticOutputMixin[RestoreProjectPayloadDTO]):
    """Payload for project restore."""

    restored: bool = gql_field(
        description="Whether the restore was successful.",
        deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `project`.",
    )
    project: ProjectV2GQL = gql_added_field(
        BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="The restored project."),
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for project permanent deletion mutation.",
    ),
    model=PurgeProjectPayloadDTO,
    name="PurgeProjectPayload",
)
class PurgeProjectPayloadGQL(PydanticOutputMixin[PurgeProjectPayloadDTO]):
    """Payload for project permanent purge."""

    purged: bool = gql_field(description="Whether the purge was successful.")


# --- Unassign Users ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for unassigning users from a project.",
    ),
    name="UnassignUsersFromProjectInput",
)
class UnassignUsersFromProjectInputGQL(PydanticInputMixin[UnassignUsersFromProjectInputDTO]):
    """Input for unassigning users from a project."""

    user_ids: list[UUID] = gql_field(description="List of user UUIDs to unassign from the project.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk project operation: the projects processed and the ones "
            "that failed."
        ),
    ),
    model=PartialBulkPayload[ProjectNode],
    name="PartialBulkProjectsPayload",
)
class PartialBulkProjectsPayloadGQL(PydanticOutputMixin[PartialBulkPayload[ProjectNode]]):
    """Payload for partial bulk project mutations."""

    successes: list[ProjectV2GQL] = gql_field(
        description="The projects processed, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The projects not processed, each with the reason."
    )
