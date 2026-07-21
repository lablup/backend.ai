from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.retention_policy.request import (
    CreateRetentionPolicyInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    RetentionPolicyFilter as FilterDTO,
)
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    RetentionPolicyOrder as OrderDTO,
)
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    UpdateRetentionPolicyInput as UpdateInputDTO,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    CreateRetentionPolicyPayload as CreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    DeleteRetentionPolicyPayload as DeletePayloadDTO,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    PurgeRetentionPolicyPayload as PurgePayloadDTO,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    RetentionPolicyNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    UpdateRetentionPolicyPayload as UpdatePayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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
        description="Retention category identifying a code-side cleanup procedure.",
    ),
    name="RetentionCategory",
)
class RetentionCategoryGQL(StrEnum):
    LOGS = "logs"
    LOGIN = "login"
    RECONCILE_HISTORY = "reconcile_history"
    ROLES_INVITATIONS = "roles_invitations"
    DEPLOYMENTS = "deployments"
    SESSIONS = "sessions"
    USAGE_RECORDS = "usage_records"
    USAGE_BUCKETS = "usage_buckets"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Order fields for retention policies.",
    ),
    name="RetentionPolicyOrderField",
)
class RetentionPolicyOrderFieldGQL(StrEnum):
    CATEGORY = "category"
    CREATED_AT = "created_at"
    LAST_SWEPT_AT = "last_swept_at"


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A per-category retention policy: admin-tunable cleanup settings for accumulating DB records.",
    ),
    name="RetentionPolicy",
)
class RetentionPolicyGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    category: RetentionCategoryGQL = gql_field(description="Retention category.")
    retention_period_days: int = gql_field(
        description="Retention period in days; records older than now - period are purged."
    )
    enabled: bool = gql_field(description="Whether this policy is active.")
    last_swept_at: datetime | None = gql_field(
        description="When this policy was last swept (read-only observability field)."
    )
    created_at: datetime = gql_field(description="Timestamp when this policy was created.")
    updated_at: datetime = gql_field(description="Timestamp of the last modification.")


RetentionPolicyEdge = Edge[RetentionPolicyGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated list of retention policies.",
    )
)
class RetentionPolicyConnection(Connection[RetentionPolicyGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Filter for retention policies."
    ),
    name="RetentionPolicyFilter",
)
class RetentionPolicyFilterGQL(PydanticInputMixin[FilterDTO]):
    category: RetentionCategoryGQL | None = gql_field(default=None, description="Category filter.")
    enabled: bool | None = gql_field(default=None, description="Enabled filter.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Order specification."),
    name="RetentionPolicyOrderBy",
)
class RetentionPolicyOrderByGQL(PydanticInputMixin[OrderDTO]):
    field: RetentionPolicyOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Create retention policy input."
    ),
    name="CreateRetentionPolicyInput",
)
class CreateRetentionPolicyInputGQL(PydanticInputMixin[CreateInputDTO]):
    category: RetentionCategoryGQL = gql_field(
        description="Retention category, validated against the fixed catalog."
    )
    retention_period_days: int = gql_field(description="Retention period in days.")
    enabled: bool = gql_field(default=True, description="Whether this policy is active.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Update retention policy input."
    ),
    name="UpdateRetentionPolicyInput",
)
class UpdateRetentionPolicyInputGQL(PydanticInputMixin[UpdateInputDTO]):
    id: UUID = gql_field(description="Retention policy ID.")
    category: RetentionCategoryGQL | None = gql_field(default=None, description="New category.")
    retention_period_days: int | None = gql_field(
        default=None, description="New retention period in days."
    )
    enabled: bool | None = gql_field(default=None, description="Toggle enabled.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Create retention policy payload."
    ),
    model=CreatePayloadDTO,
    name="CreateRetentionPolicyPayload",
)
class CreateRetentionPolicyPayloadGQL(PydanticOutputMixin[CreatePayloadDTO]):
    policy: RetentionPolicyGQL = gql_field(description="The created retention policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Update retention policy payload."
    ),
    model=UpdatePayloadDTO,
    name="UpdateRetentionPolicyPayload",
)
class UpdateRetentionPolicyPayloadGQL(PydanticOutputMixin[UpdatePayloadDTO]):
    policy: RetentionPolicyGQL = gql_field(description="The updated retention policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Delete retention policy payload."
    ),
    model=DeletePayloadDTO,
    name="DeleteRetentionPolicyPayload",
)
class DeleteRetentionPolicyPayloadGQL(PydanticOutputMixin[DeletePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted retention policy.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Purge retention policy payload."
    ),
    model=PurgePayloadDTO,
    name="PurgeRetentionPolicyPayload",
)
class PurgeRetentionPolicyPayloadGQL(PydanticOutputMixin[PurgePayloadDTO]):
    id: UUID = gql_field(description="ID of the purged retention policy.")
