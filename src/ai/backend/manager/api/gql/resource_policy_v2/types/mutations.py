"""Resource Policy V2 GraphQL mutation input and payload types."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import UNSET

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
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
    PartialBulkPurgeKeypairResourcePoliciesInput as PartialBulkPurgeKeypairResourcePoliciesInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    PartialBulkPurgeProjectResourcePoliciesInput as PartialBulkPurgeProjectResourcePoliciesInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    PartialBulkPurgeUserResourcePoliciesInput as PartialBulkPurgeUserResourcePoliciesInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    PartialBulkUpdateKeypairResourcePoliciesInput as PartialBulkUpdateKeypairResourcePoliciesInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    PartialBulkUpdateKeypairResourcePolicyItemInput as PartialBulkUpdateKeypairResourcePolicyItemInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    PartialBulkUpdateProjectResourcePoliciesInput as PartialBulkUpdateProjectResourcePoliciesInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    PartialBulkUpdateProjectResourcePolicyItemInput as PartialBulkUpdateProjectResourcePolicyItemInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    PartialBulkUpdateUserResourcePoliciesInput as PartialBulkUpdateUserResourcePoliciesInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    PartialBulkUpdateUserResourcePolicyItemInput as PartialBulkUpdateUserResourcePolicyItemInputDTO,
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
    KeypairResourcePolicyNode,
    ProjectResourcePolicyNode,
    UserResourcePolicyNode,
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
    PartialBulkFailureGQL,
    ResourceSlotEntryInputGQL,
    VFolderHostPermissionEntryInputGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
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

# ── Keypair Resource Policy Inputs ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for creating a keypair resource policy.",
    ),
    name="CreateKeypairResourcePolicyInput",
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
        default=None, description="Maximum pending sessions. Null means unlimited."
    )
    max_priority: int | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.8.0",
            description=(
                "Highest scheduling priority a session created with this policy may declare."
                " Null means uncapped."
            ),
        ),
        default=None,
    )
    max_pending_session_resource_slots: list[ResourceSlotEntryInputGQL] | None = gql_field(
        default=None, description="Maximum pending session resource slots."
    )
    max_concurrent_sftp_sessions: int = gql_field(
        default=1, description="Maximum concurrent SFTP sessions."
    )
    allowed_vfolder_hosts: list[VFolderHostPermissionEntryInputGQL] = gql_field(
        description="Allowed vfolder host permissions."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for updating a keypair resource policy. All fields optional.",
    ),
    name="UpdateKeypairResourcePolicyInput",
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
    max_priority: int | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.8.0",
            description="Updated max scheduling priority. Set to null to clear (uncapped).",
        ),
        default=UNSET,
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
        added_version="26.4.2",
        description="Input for creating a user resource policy.",
    ),
    name="CreateUserResourcePolicyInputV2",
)
class CreateUserResourcePolicyInputGQL(PydanticInputMixin[CreateUserResourcePolicyInputDTO]):
    name: str = gql_field(description="Policy name. Must be unique.")
    max_vfolder_count: int = gql_field(description="Maximum vfolders a user can create.")
    max_concurrent_logins: int | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
            description=(
                "Maximum number of concurrent authenticated login sessions per user."
                " Null means unlimited."
                " Distinct from keypair_resource_policies.max_concurrent_sessions"
                " which caps compute sessions."
            ),
        ),
        default=None,
    )
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
        added_version="26.4.2",
        description="Input for updating a user resource policy. All fields optional.",
    ),
    name="UpdateUserResourcePolicyInput",
)
class UpdateUserResourcePolicyInputGQL(PydanticInputMixin[UpdateUserResourcePolicyInputDTO]):
    max_vfolder_count: int | None = gql_field(
        default=UNSET, description="Updated max vfolder count."
    )
    max_concurrent_logins: int | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
            description=(
                "Updated maximum number of concurrent authenticated login sessions per user."
                " Set to null to clear (unlimited)."
                " Distinct from keypair_resource_policies.max_concurrent_sessions"
                " which caps compute sessions."
            ),
        ),
        default=UNSET,
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
        added_version="26.4.2",
        description="Input for creating a project resource policy.",
    ),
    name="CreateProjectResourcePolicyInputV2",
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
        added_version="26.4.2",
        description="Input for updating a project resource policy. All fields optional.",
    ),
    name="UpdateProjectResourcePolicyInput",
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One keypair resource policy of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateKeypairResourcePolicyItemInput",
)
class PartialBulkUpdateKeypairResourcePolicyItemInputGQL(
    PydanticInputMixin[PartialBulkUpdateKeypairResourcePolicyItemInputDTO]
):
    id: UUID = gql_field(description="ID of the keypair resource policy to update.")
    input: UpdateKeypairResourcePolicyInputGQL = gql_field(
        description="Fields to update on the policy."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for updating several keypair resource policies, each answered for separately."
        ),
    ),
    name="PartialBulkUpdateKeypairResourcePoliciesInput",
)
class PartialBulkUpdateKeypairResourcePoliciesInputGQL(
    PydanticInputMixin[PartialBulkUpdateKeypairResourcePoliciesInputDTO]
):
    items: list[PartialBulkUpdateKeypairResourcePolicyItemInputGQL] = gql_field(
        description="The keypair resource policies to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for purging several keypair resource policies, each answered for separately."
        ),
    ),
    name="PartialBulkPurgeKeypairResourcePoliciesInput",
)
class PartialBulkPurgeKeypairResourcePoliciesInputGQL(
    PydanticInputMixin[PartialBulkPurgeKeypairResourcePoliciesInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the keypair resource policies to purge.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One user resource policy of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateUserResourcePolicyItemInput",
)
class PartialBulkUpdateUserResourcePolicyItemInputGQL(
    PydanticInputMixin[PartialBulkUpdateUserResourcePolicyItemInputDTO]
):
    id: UUID = gql_field(description="ID of the user resource policy to update.")
    input: UpdateUserResourcePolicyInputGQL = gql_field(
        description="Fields to update on the policy."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for updating several user resource policies, each answered for separately."
        ),
    ),
    name="PartialBulkUpdateUserResourcePoliciesInput",
)
class PartialBulkUpdateUserResourcePoliciesInputGQL(
    PydanticInputMixin[PartialBulkUpdateUserResourcePoliciesInputDTO]
):
    items: list[PartialBulkUpdateUserResourcePolicyItemInputGQL] = gql_field(
        description="The user resource policies to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for purging several user resource policies, each answered for separately."
        ),
    ),
    name="PartialBulkPurgeUserResourcePoliciesInput",
)
class PartialBulkPurgeUserResourcePoliciesInputGQL(
    PydanticInputMixin[PartialBulkPurgeUserResourcePoliciesInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the user resource policies to purge.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One project resource policy of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateProjectResourcePolicyItemInput",
)
class PartialBulkUpdateProjectResourcePolicyItemInputGQL(
    PydanticInputMixin[PartialBulkUpdateProjectResourcePolicyItemInputDTO]
):
    id: UUID = gql_field(description="ID of the project resource policy to update.")
    input: UpdateProjectResourcePolicyInputGQL = gql_field(
        description="Fields to update on the policy."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for updating several project resource policies, each answered for separately."
        ),
    ),
    name="PartialBulkUpdateProjectResourcePoliciesInput",
)
class PartialBulkUpdateProjectResourcePoliciesInputGQL(
    PydanticInputMixin[PartialBulkUpdateProjectResourcePoliciesInputDTO]
):
    items: list[PartialBulkUpdateProjectResourcePolicyItemInputGQL] = gql_field(
        description="The project resource policies to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for purging several project resource policies, each answered for separately."
        ),
    ),
    name="PartialBulkPurgeProjectResourcePoliciesInput",
)
class PartialBulkPurgeProjectResourcePoliciesInputGQL(
    PydanticInputMixin[PartialBulkPurgeProjectResourcePoliciesInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the project resource policies to purge.")


# ── Payloads ──


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for keypair resource policy create/update mutations.",
    ),
    model=CreateKeypairResourcePolicyPayloadDTO,
    name="CreateKeypairResourcePolicyPayload",
)
class CreateKeypairResourcePolicyPayloadGQL(
    PydanticOutputMixin[CreateKeypairResourcePolicyPayloadDTO]
):
    keypair_resource_policy: KeypairResourcePolicyV2GQL = gql_field(
        description="The keypair resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for keypair resource policy update mutation.",
    ),
    model=UpdateKeypairResourcePolicyPayloadDTO,
    name="UpdateKeypairResourcePolicyPayload",
)
class UpdateKeypairResourcePolicyPayloadGQL(
    PydanticOutputMixin[UpdateKeypairResourcePolicyPayloadDTO]
):
    keypair_resource_policy: KeypairResourcePolicyV2GQL = gql_field(
        description="The updated keypair resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for keypair resource policy deletion.",
    ),
    model=DeleteKeypairResourcePolicyPayloadDTO,
    name="DeleteKeypairResourcePolicyPayload",
)
class DeleteKeypairResourcePolicyPayloadGQL(
    PydanticOutputMixin[DeleteKeypairResourcePolicyPayloadDTO]
):
    name: str = gql_field(description="Name of the deleted policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for keypair resource policy purge.",
    ),
    model=DeleteKeypairResourcePolicyPayloadDTO,
    name="PurgeKeypairResourcePolicyPayload",
)
class PurgeKeypairResourcePolicyPayloadGQL(
    PydanticOutputMixin[DeleteKeypairResourcePolicyPayloadDTO]
):
    purged_id: strawberry.ID = gql_field(
        description="Global ID of the purged keypair resource policy."
    )
    entity_id: UUID = gql_field(description="UUID of the purged keypair resource policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for user resource policy create/update mutations.",
    ),
    model=CreateUserResourcePolicyPayloadDTO,
    name="CreateUserResourcePolicyPayload",
)
class CreateUserResourcePolicyPayloadGQL(PydanticOutputMixin[CreateUserResourcePolicyPayloadDTO]):
    user_resource_policy: UserResourcePolicyV2GQL = gql_field(
        description="The user resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for user resource policy update mutation.",
    ),
    model=UpdateUserResourcePolicyPayloadDTO,
    name="UpdateUserResourcePolicyPayload",
)
class UpdateUserResourcePolicyPayloadGQL(PydanticOutputMixin[UpdateUserResourcePolicyPayloadDTO]):
    user_resource_policy: UserResourcePolicyV2GQL = gql_field(
        description="The updated user resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for user resource policy deletion.",
    ),
    model=DeleteUserResourcePolicyPayloadDTO,
    name="DeleteUserResourcePolicyPayload",
)
class DeleteUserResourcePolicyPayloadGQL(PydanticOutputMixin[DeleteUserResourcePolicyPayloadDTO]):
    name: str = gql_field(description="Name of the deleted policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for user resource policy purge.",
    ),
    model=DeleteUserResourcePolicyPayloadDTO,
    name="PurgeUserResourcePolicyPayload",
)
class PurgeUserResourcePolicyPayloadGQL(PydanticOutputMixin[DeleteUserResourcePolicyPayloadDTO]):
    purged_id: strawberry.ID = gql_field(
        description="Global ID of the purged user resource policy."
    )
    entity_id: UUID = gql_field(description="UUID of the purged user resource policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for project resource policy create/update mutations.",
    ),
    model=CreateProjectResourcePolicyPayloadDTO,
    name="CreateProjectResourcePolicyPayload",
)
class CreateProjectResourcePolicyPayloadGQL(
    PydanticOutputMixin[CreateProjectResourcePolicyPayloadDTO]
):
    project_resource_policy: ProjectResourcePolicyV2GQL = gql_field(
        description="The project resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for project resource policy update mutation.",
    ),
    model=UpdateProjectResourcePolicyPayloadDTO,
    name="UpdateProjectResourcePolicyPayload",
)
class UpdateProjectResourcePolicyPayloadGQL(
    PydanticOutputMixin[UpdateProjectResourcePolicyPayloadDTO]
):
    project_resource_policy: ProjectResourcePolicyV2GQL = gql_field(
        description="The updated project resource policy."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for project resource policy deletion.",
    ),
    model=DeleteProjectResourcePolicyPayloadDTO,
    name="DeleteProjectResourcePolicyPayload",
)
class DeleteProjectResourcePolicyPayloadGQL(
    PydanticOutputMixin[DeleteProjectResourcePolicyPayloadDTO]
):
    name: str = gql_field(description="Name of the deleted policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for project resource policy purge.",
    ),
    model=DeleteProjectResourcePolicyPayloadDTO,
    name="PurgeProjectResourcePolicyPayload",
)
class PurgeProjectResourcePolicyPayloadGQL(
    PydanticOutputMixin[DeleteProjectResourcePolicyPayloadDTO]
):
    purged_id: strawberry.ID = gql_field(
        description="Global ID of the purged project resource policy."
    )
    entity_id: UUID = gql_field(description="UUID of the purged project resource policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk keypair resource policy operation: the policies processed "
            "and the ones that failed."
        ),
    ),
    model=PartialBulkPayload[KeypairResourcePolicyNode],
    name="PartialBulkKeypairResourcePoliciesPayload",
)
class PartialBulkKeypairResourcePoliciesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[KeypairResourcePolicyNode]]
):
    """Payload for partial bulk keypair resource policy mutations."""

    successes: list[KeypairResourcePolicyV2GQL] = gql_field(
        description="The policies processed, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The policies not processed, each with the reason."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk user resource policy operation: the policies processed "
            "and the ones that failed."
        ),
    ),
    model=PartialBulkPayload[UserResourcePolicyNode],
    name="PartialBulkUserResourcePoliciesPayload",
)
class PartialBulkUserResourcePoliciesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[UserResourcePolicyNode]]
):
    """Payload for partial bulk user resource policy mutations."""

    successes: list[UserResourcePolicyV2GQL] = gql_field(
        description="The policies processed, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The policies not processed, each with the reason."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk project resource policy operation: the policies processed "
            "and the ones that failed."
        ),
    ),
    model=PartialBulkPayload[ProjectResourcePolicyNode],
    name="PartialBulkProjectResourcePoliciesPayload",
)
class PartialBulkProjectResourcePoliciesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[ProjectResourcePolicyNode]]
):
    """Payload for partial bulk project resource policy mutations."""

    successes: list[ProjectResourcePolicyV2GQL] = gql_field(
        description="The policies processed, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The policies not processed, each with the reason."
    )
