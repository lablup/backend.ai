"""Resource Policy V2 GraphQL mutation input and payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.resource_policy.request import (
    CreateKeypairResourcePolicyInput as CreateKeypairResourcePolicyInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    CreateProjectResourcePolicyInput as CreateProjectResourcePolicyInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    CreateUserResourcePolicyInput as CreateUserResourcePolicyInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UpdateKeypairResourcePolicyInput as UpdateKeypairResourcePolicyInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UpdateProjectResourcePolicyInput as UpdateProjectResourcePolicyInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UpdateUserResourcePolicyInput as UpdateUserResourcePolicyInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateKeypairResourcePolicyPayload as CreateKeypairResourcePolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateProjectResourcePolicyPayload as CreateProjectResourcePolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateUserResourcePolicyPayload as CreateUserResourcePolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    DeleteKeypairResourcePolicyPayload as DeleteKeypairResourcePolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    DeleteProjectResourcePolicyPayload as DeleteProjectResourcePolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    DeleteUserResourcePolicyPayload as DeleteUserResourcePolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    UpdateKeypairResourcePolicyPayload as UpdateKeypairResourcePolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    UpdateProjectResourcePolicyPayload as UpdateProjectResourcePolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    UpdateUserResourcePolicyPayload as UpdateUserResourcePolicyPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import (
    BinarySizeInputGQL,
    ResourceSlotEntryInputGQL,
    VFolderHostPermissionEntryInputGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

from .node import (
    KeypairResourcePolicyV2GQL,
    ProjectResourcePolicyV2GQL,
    UserResourcePolicyV2GQL,
)

UNSET = None


# ── Keypair Resource Policy Inputs ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating a keypair resource policy.",
    )
)
class CreateKeypairResourcePolicyInputGQL(PydanticInputMixin[CreateKeypairResourcePolicyInputDTO]):
    name: str = gql_field(description="Policy name. Must be unique.")
    default_for_unspecified: str = gql_field(
        description="Default for unspecified resource slots (LIMITED or UNLIMITED)."
    )
    total_resource_slots: list[ResourceSlotEntryInputGQL] = gql_field(
        description="Total resource slot limits."
    )
    max_session_lifetime: int = gql_field(description="Maximum session lifetime in seconds.")
    max_concurrent_sessions: int = gql_field(description="Maximum concurrent sessions.")
    max_containers_per_session: int = gql_field(description="Maximum containers per session.")
    idle_timeout: int = gql_field(description="Idle timeout in seconds.")
    max_pending_session_count: int | None = gql_field(
        default=UNSET, description="Maximum pending sessions. Null means unlimited."
    )
    max_pending_session_resource_slots: list[ResourceSlotEntryInputGQL] | None = gql_field(
        default=UNSET, description="Maximum pending session resource slots."
    )
    max_concurrent_sftp_sessions: int = gql_field(
        default=1, description="Maximum concurrent SFTP sessions."
    )
    allowed_vfolder_hosts: list[VFolderHostPermissionEntryInputGQL] = gql_field(
        description="Allowed vfolder host permissions."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating a keypair resource policy. All fields optional.",
    )
)
class UpdateKeypairResourcePolicyInputGQL(PydanticInputMixin[UpdateKeypairResourcePolicyInputDTO]):
    default_for_unspecified: str | None = gql_field(
        default=UNSET, description="Updated default for unspecified."
    )
    total_resource_slots: list[ResourceSlotEntryInputGQL] | None = gql_field(
        default=UNSET, description="Updated resource slot limits."
    )
    max_session_lifetime: int | None = gql_field(
        default=UNSET, description="Updated max session lifetime."
    )
    max_concurrent_sessions: int | None = gql_field(
        default=UNSET, description="Updated max concurrent sessions."
    )
    max_pending_session_count: int | None = gql_field(
        default=UNSET, description="Updated max pending sessions."
    )
    max_pending_session_resource_slots: list[ResourceSlotEntryInputGQL] | None = gql_field(
        default=UNSET, description="Updated max pending session resource slots."
    )
    max_concurrent_sftp_sessions: int | None = gql_field(
        default=UNSET, description="Updated max concurrent SFTP sessions."
    )
    max_containers_per_session: int | None = gql_field(
        default=UNSET, description="Updated max containers per session."
    )
    idle_timeout: int | None = gql_field(default=UNSET, description="Updated idle timeout.")
    allowed_vfolder_hosts: list[VFolderHostPermissionEntryInputGQL] | None = gql_field(
        default=UNSET, description="Updated vfolder host permissions."
    )


# ── User Resource Policy Inputs ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating a user resource policy.",
    )
)
class CreateUserResourcePolicyInputGQL(PydanticInputMixin[CreateUserResourcePolicyInputDTO]):
    name: str = gql_field(description="Policy name. Must be unique.")
    max_vfolder_count: int = gql_field(description="Maximum vfolders a user can create.")
    max_quota_scope_size: BinarySizeInputGQL = gql_field(
        description="Maximum quota scope size (e.g., '1g', '536870912').",
    )
    max_session_count_per_model_session: int = gql_field(
        description="Maximum sessions per model session."
    )
    max_customized_image_count: int = gql_field(
        description="Maximum customized images a user can create."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating a user resource policy. All fields optional.",
    )
)
class UpdateUserResourcePolicyInputGQL(PydanticInputMixin[UpdateUserResourcePolicyInputDTO]):
    max_vfolder_count: int | None = gql_field(
        default=UNSET, description="Updated max vfolder count."
    )
    max_quota_scope_size: BinarySizeInputGQL | None = gql_field(
        default=UNSET, description="Updated max quota scope size."
    )
    max_session_count_per_model_session: int | None = gql_field(
        default=UNSET, description="Updated max sessions per model session."
    )
    max_customized_image_count: int | None = gql_field(
        default=UNSET, description="Updated max customized image count."
    )


# ── Project Resource Policy Inputs ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating a project resource policy.",
    )
)
class CreateProjectResourcePolicyInputGQL(PydanticInputMixin[CreateProjectResourcePolicyInputDTO]):
    name: str = gql_field(description="Policy name. Must be unique.")
    max_vfolder_count: int = gql_field(description="Maximum vfolders a project can have.")
    max_quota_scope_size: BinarySizeInputGQL = gql_field(
        description="Maximum quota scope size (e.g., '1g', '536870912').",
    )
    max_network_count: int = gql_field(
        description="Maximum networks a project can create. -1 means unlimited."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating a project resource policy. All fields optional.",
    )
)
class UpdateProjectResourcePolicyInputGQL(PydanticInputMixin[UpdateProjectResourcePolicyInputDTO]):
    max_vfolder_count: int | None = gql_field(
        default=UNSET, description="Updated max vfolder count."
    )
    max_quota_scope_size: BinarySizeInputGQL | None = gql_field(
        default=UNSET, description="Updated max quota scope size."
    )
    max_network_count: int | None = gql_field(
        default=UNSET, description="Updated max network count."
    )


# ── Payloads ──


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for keypair resource policy create/update mutations.",
    ),
    model=CreateKeypairResourcePolicyPayloadDTO,
)
class CreateKeypairResourcePolicyPayloadGQL(
    PydanticOutputMixin[CreateKeypairResourcePolicyPayloadDTO]
):
    keypair_resource_policy: KeypairResourcePolicyV2GQL = gql_field(
        description="The keypair resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for keypair resource policy update mutation.",
    ),
    model=UpdateKeypairResourcePolicyPayloadDTO,
)
class UpdateKeypairResourcePolicyPayloadGQL(
    PydanticOutputMixin[UpdateKeypairResourcePolicyPayloadDTO]
):
    keypair_resource_policy: KeypairResourcePolicyV2GQL = gql_field(
        description="The updated keypair resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for keypair resource policy deletion.",
    ),
    model=DeleteKeypairResourcePolicyPayloadDTO,
)
class DeleteKeypairResourcePolicyPayloadGQL(
    PydanticOutputMixin[DeleteKeypairResourcePolicyPayloadDTO]
):
    name: str = gql_field(description="Name of the deleted policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for user resource policy create/update mutations.",
    ),
    model=CreateUserResourcePolicyPayloadDTO,
)
class CreateUserResourcePolicyPayloadGQL(PydanticOutputMixin[CreateUserResourcePolicyPayloadDTO]):
    user_resource_policy: UserResourcePolicyV2GQL = gql_field(
        description="The user resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for user resource policy update mutation.",
    ),
    model=UpdateUserResourcePolicyPayloadDTO,
)
class UpdateUserResourcePolicyPayloadGQL(PydanticOutputMixin[UpdateUserResourcePolicyPayloadDTO]):
    user_resource_policy: UserResourcePolicyV2GQL = gql_field(
        description="The updated user resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for user resource policy deletion.",
    ),
    model=DeleteUserResourcePolicyPayloadDTO,
)
class DeleteUserResourcePolicyPayloadGQL(PydanticOutputMixin[DeleteUserResourcePolicyPayloadDTO]):
    name: str = gql_field(description="Name of the deleted policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for project resource policy create/update mutations.",
    ),
    model=CreateProjectResourcePolicyPayloadDTO,
)
class CreateProjectResourcePolicyPayloadGQL(
    PydanticOutputMixin[CreateProjectResourcePolicyPayloadDTO]
):
    project_resource_policy: ProjectResourcePolicyV2GQL = gql_field(
        description="The project resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for project resource policy update mutation.",
    ),
    model=UpdateProjectResourcePolicyPayloadDTO,
)
class UpdateProjectResourcePolicyPayloadGQL(
    PydanticOutputMixin[UpdateProjectResourcePolicyPayloadDTO]
):
    project_resource_policy: ProjectResourcePolicyV2GQL = gql_field(
        description="The updated project resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for project resource policy deletion.",
    ),
    model=DeleteProjectResourcePolicyPayloadDTO,
)
class DeleteProjectResourcePolicyPayloadGQL(
    PydanticOutputMixin[DeleteProjectResourcePolicyPayloadDTO]
):
    name: str = gql_field(description="Name of the deleted policy.")
