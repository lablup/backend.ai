"""GQL types for role invitations."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.role_invitation.request import (
    AcceptRoleInvitationInput as AcceptRoleInvitationInputDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    CancelRoleInvitationInput as CancelRoleInvitationInputDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    CreateRoleInvitationInput as CreateRoleInvitationInputDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    RejectRoleInvitationInput as RejectRoleInvitationInputDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    RoleInvitationFilter as RoleInvitationFilterDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    RoleInvitationOrderBy as RoleInvitationOrderByDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    RoleInvitationStateFilter as RoleInvitationStateFilterDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    RoleNestedFilter as RoleNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    UserNestedFilter as UserNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.response import (
    CreateRoleInvitationPayload as CreateRoleInvitationPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.response import (
    RoleInvitationNode as RoleInvitationNodeDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
    PydanticOutputMixin,
)
from ai.backend.manager.api.gql.types import GQLOrderBy

# -- Enums --


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Role invitation state.",
    ),
    name="RoleInvitationState",
)
class RoleInvitationStateGQL(StrEnum):
    """GraphQL enum for role invitation state.

    Kept separate from `RoleInvitationStateDTO` with matching values; the Pydantic
    compatibility layer performs 1:1 conversion via `.value` coercion.
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Role invitation ordering field.",
    ),
    name="RoleInvitationOrderField",
)
class RoleInvitationOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATE = "state"


# -- Node --


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A role invitation.",
    ),
    name="RoleInvitation",
)
class RoleInvitationGQL(PydanticNodeMixin[RoleInvitationNodeDTO]):
    id: NodeID[str]
    inviter_user_id: UUID | None = gql_field(description="Inviter user ID.")
    invitee_user_id: UUID = gql_field(description="Invitee user ID.")
    role_id: UUID = gql_field(description="Role ID.")
    state: RoleInvitationStateGQL = gql_field(description="Invitation state.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")


# -- Connection --

RoleInvitationEdge = Edge[RoleInvitationGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Role invitation connection.",
    )
)
class RoleInvitationConnection(Connection[RoleInvitationGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# -- OrderBy --


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Order by specification for role invitations.",
    ),
    name="RoleInvitationOrderBy",
)
class RoleInvitationOrderByGQL(PydanticInputMixin[RoleInvitationOrderByDTO], GQLOrderBy):
    field: RoleInvitationOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC


# -- Filters --


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for role invitation state.",
    ),
    name="RoleInvitationStateFilter",
)
class RoleInvitationStateFilterGQL(PydanticInputMixin[RoleInvitationStateFilterDTO]):
    equals: RoleInvitationStateGQL | None = None
    in_: list[RoleInvitationStateGQL] | None = gql_field(
        description="Match any of the provided states.", name="in", default=None
    )
    not_equals: RoleInvitationStateGQL | None = gql_field(
        description="Exclude exact state match.", name="notEquals", default=None
    )
    not_in: list[RoleInvitationStateGQL] | None = gql_field(
        description="Exclude any of the provided states.", name="notIn", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Nested filter for the role associated with an invitation.",
    ),
    name="RoleInvitationRoleNestedFilter",
)
class RoleInvitationRoleNestedFilterGQL(PydanticInputMixin[RoleNestedFilterDTO]):
    name: StringFilter | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Nested filter for a user (inviter or invitee) of an invitation.",
    ),
    name="RoleInvitationUserNestedFilter",
)
class RoleInvitationUserNestedFilterGQL(PydanticInputMixin[UserNestedFilterDTO]):
    email: StringFilter | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for role invitations.",
    ),
    name="RoleInvitationFilter",
)
class RoleInvitationFilterGQL(PydanticInputMixin[RoleInvitationFilterDTO]):
    state: RoleInvitationStateFilterGQL | None = None
    role_id: UUIDFilter | None = None
    role: RoleInvitationRoleNestedFilterGQL | None = None
    inviter: RoleInvitationUserNestedFilterGQL | None = None
    invitee: RoleInvitationUserNestedFilterGQL | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


# -- Inputs --


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating role invitations.",
    ),
    name="CreateRoleInvitationInput",
)
class CreateRoleInvitationInputGQL(PydanticInputMixin[CreateRoleInvitationInputDTO]):
    role_id: UUID
    emails: list[str]


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for accepting a role invitation.",
    ),
    name="AcceptRoleInvitationInput",
)
class AcceptRoleInvitationInputGQL(PydanticInputMixin[AcceptRoleInvitationInputDTO]):
    invitation_id: UUID


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for rejecting a role invitation.",
    ),
    name="RejectRoleInvitationInput",
)
class RejectRoleInvitationInputGQL(PydanticInputMixin[RejectRoleInvitationInputDTO]):
    invitation_id: UUID


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for canceling a role invitation.",
    ),
    name="CancelRoleInvitationInput",
)
class CancelRoleInvitationInputGQL(PydanticInputMixin[CancelRoleInvitationInputDTO]):
    invitation_id: UUID


# -- Payloads --


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for role invitation creation.",
    ),
    model=CreateRoleInvitationPayloadDTO,
    name="CreateRoleInvitationPayload",
)
class CreateRoleInvitationPayload(PydanticOutputMixin[CreateRoleInvitationPayloadDTO]):
    items: list[RoleInvitationGQL] = gql_field(description="List of created role invitations.")
