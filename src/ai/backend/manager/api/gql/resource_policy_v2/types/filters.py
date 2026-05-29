"""Resource Policy V2 GraphQL filter and order types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.resource_policy.request import (
    KeypairResourcePolicyFilter as KeypairResourcePolicyFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    KeypairResourcePolicyKeypairNestedFilter as KeypairResourcePolicyKeypairNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    KeypairResourcePolicyOrder as KeypairResourcePolicyOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    ProjectResourcePolicyFilter as ProjectResourcePolicyFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    ProjectResourcePolicyOrder as ProjectResourcePolicyOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UserResourcePolicyFilter as UserResourcePolicyFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UserResourcePolicyOrder as UserResourcePolicyOrderDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    IntFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

# ── Keypair Resource Policy ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Nested filter for keypairs assigned to a keypair resource policy. "
            "Filters policies linked to at least one keypair matching all specified conditions."
        ),
    ),
    name="KeypairResourcePolicyKeypairNestedFilter",
)
class KeypairResourcePolicyKeypairNestedFilterGQL(
    PydanticInputMixin[KeypairResourcePolicyKeypairNestedFilterDTO]
):
    user_id: UUIDFilter | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Filter for keypair resource policies.",
    ),
    name="KeypairResourcePolicyV2Filter",
)
class KeypairResourcePolicyV2Filter(PydanticInputMixin[KeypairResourcePolicyFilterDTO]):
    name: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    max_session_lifetime: IntFilter | None = None
    max_concurrent_sessions: IntFilter | None = None
    max_containers_per_session: IntFilter | None = None
    idle_timeout: IntFilter | None = None
    max_concurrent_sftp_sessions: IntFilter | None = None
    max_pending_session_count: IntFilter | None = None
    keypair: KeypairResourcePolicyKeypairNestedFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "Filter policies by their assigned keypairs "
                "(e.g., policies linked to keypairs owned by a specific user)."
            ),
        ),
        default=None,
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Fields available for ordering keypair resource policies.",
    ),
    name="KeypairResourcePolicyV2OrderField",
)
class KeypairResourcePolicyV2OrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    MAX_SESSION_LIFETIME = "max_session_lifetime"
    MAX_CONCURRENT_SESSIONS = "max_concurrent_sessions"
    MAX_CONTAINERS_PER_SESSION = "max_containers_per_session"
    IDLE_TIMEOUT = "idle_timeout"
    MAX_CONCURRENT_SFTP_SESSIONS = "max_concurrent_sftp_sessions"
    MAX_PENDING_SESSION_COUNT = "max_pending_session_count"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Ordering specification for keypair resource policies.",
    ),
    name="KeypairResourcePolicyV2OrderBy",
)
class KeypairResourcePolicyV2OrderBy(PydanticInputMixin[KeypairResourcePolicyOrderDTO]):
    field: KeypairResourcePolicyV2OrderField = gql_field(
        default=KeypairResourcePolicyV2OrderField.CREATED_AT, description="Field to order by."
    )
    direction: OrderDirection = gql_field(
        default=OrderDirection.DESC, description="Sort direction."
    )


# ── User Resource Policy ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Filter for user resource policies.",
    ),
    name="UserResourcePolicyV2Filter",
)
class UserResourcePolicyV2Filter(PydanticInputMixin[UserResourcePolicyFilterDTO]):
    name: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    max_vfolder_count: IntFilter | None = None
    max_concurrent_logins: IntFilter | None = None
    max_quota_scope_size: IntFilter | None = None
    max_session_count_per_model_session: IntFilter | None = None
    max_customized_image_count: IntFilter | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Fields available for ordering user resource policies.",
    ),
    name="UserResourcePolicyV2OrderField",
)
class UserResourcePolicyV2OrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    MAX_VFOLDER_COUNT = "max_vfolder_count"
    MAX_CONCURRENT_LOGINS = "max_concurrent_logins"
    MAX_QUOTA_SCOPE_SIZE = "max_quota_scope_size"
    MAX_SESSION_COUNT_PER_MODEL_SESSION = "max_session_count_per_model_session"
    MAX_CUSTOMIZED_IMAGE_COUNT = "max_customized_image_count"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Ordering specification for user resource policies.",
    ),
    name="UserResourcePolicyV2OrderBy",
)
class UserResourcePolicyV2OrderBy(PydanticInputMixin[UserResourcePolicyOrderDTO]):
    field: UserResourcePolicyV2OrderField = gql_field(
        default=UserResourcePolicyV2OrderField.CREATED_AT, description="Field to order by."
    )
    direction: OrderDirection = gql_field(
        default=OrderDirection.DESC, description="Sort direction."
    )


# ── Project Resource Policy ──


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Filter for project resource policies.",
    ),
    name="ProjectResourcePolicyV2Filter",
)
class ProjectResourcePolicyV2Filter(PydanticInputMixin[ProjectResourcePolicyFilterDTO]):
    name: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    max_vfolder_count: IntFilter | None = None
    max_quota_scope_size: IntFilter | None = None
    max_network_count: IntFilter | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Fields available for ordering project resource policies.",
    ),
    name="ProjectResourcePolicyV2OrderField",
)
class ProjectResourcePolicyV2OrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    MAX_VFOLDER_COUNT = "max_vfolder_count"
    MAX_QUOTA_SCOPE_SIZE = "max_quota_scope_size"
    MAX_NETWORK_COUNT = "max_network_count"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Ordering specification for project resource policies.",
    ),
    name="ProjectResourcePolicyV2OrderBy",
)
class ProjectResourcePolicyV2OrderBy(PydanticInputMixin[ProjectResourcePolicyOrderDTO]):
    field: ProjectResourcePolicyV2OrderField = gql_field(
        default=ProjectResourcePolicyV2OrderField.CREATED_AT, description="Field to order by."
    )
    direction: OrderDirection = gql_field(
        default=OrderDirection.DESC, description="Sort direction."
    )
