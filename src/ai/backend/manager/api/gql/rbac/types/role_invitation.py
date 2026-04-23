"""GQL types for role invitations."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.role_invitation.request import (
    CreateRoleInvitationInput as CreateRoleInvitationInputDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    RoleInvitationOrderBy as RoleInvitationOrderByDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.response import (
    CreateRoleInvitationPayload as CreateRoleInvitationPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.response import (
    RoleInvitationNode as RoleInvitationNodeDTO,
)
from ai.backend.common.dto.manager.v2.role_invitation.types import RoleInvitationStateDTO
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection
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

RoleInvitationStateGQL: type[RoleInvitationStateDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Role invitation state.",
    ),
    RoleInvitationStateDTO,
    name="RoleInvitationState",
)


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


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Role invitation ordering field.",
    )
)
class RoleInvitationOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATE = "state"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Order by specification for role invitations.",
    ),
)
class RoleInvitationOrderByGQL(PydanticInputMixin[RoleInvitationOrderByDTO], GQLOrderBy):
    field: RoleInvitationOrderField
    direction: OrderDirection = OrderDirection.DESC


# -- Inputs --


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating role invitations.",
    ),
)
class CreateRoleInvitationInput(PydanticInputMixin[CreateRoleInvitationInputDTO]):
    role_id: UUID
    emails: list[str]


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
    items: list[RoleInvitationGQL] = gql_field(
        description="List of created role invitations."
    )
