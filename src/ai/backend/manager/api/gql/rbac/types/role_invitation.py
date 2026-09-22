"""Deprecated GQL types kept from the removed role invitation feature."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, override
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.rbac.response import (
    CreateRoleInvitationPayload as CreateRoleInvitationPayloadDTO,
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
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.rbac.types.role import RoleGQL
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL

_HINT = "role assignments"


def _meta(description: str) -> BackendAIGQLMeta:
    return BackendAIGQLMeta(
        added_version="26.4.4",
        description=description,
        deprecated_version=NEXT_RELEASE_VERSION,
        deprecation_hint=_HINT,
    )


# -- Enums --


@gql_enum(_meta("Role invitation state."), name="RoleInvitationState")
class RoleInvitationStateGQL(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELED = "canceled"


@gql_enum(_meta("Role invitation ordering field."), name="RoleInvitationOrderField")
class RoleInvitationOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATE = "state"


# -- Node --


@gql_node_type(_meta("A role invitation."), name="RoleInvitation")
class RoleInvitationGQL(PydanticNodeMixin[Any]):
    id: NodeID[str]
    inviter_user_id: UUID | None = gql_field(description="Inviter user ID.")
    invitee_user_id: UUID = gql_field(description="Invitee user ID.")
    role_id: UUID = gql_field(description="Role ID.")
    state: RoleInvitationStateGQL = gql_field(description="Invitation state.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        return [None for _ in node_ids]

    @gql_field(description="The user who sent this invitation. Null for system-issued invitations.")  # type: ignore[misc]
    def inviter(
        self,
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        return None

    @gql_field(
        description="The user who received this invitation. Null if the user no longer exists."
    )  # type: ignore[misc]
    def invitee(
        self,
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        return None

    @gql_field(
        description="The role this invitation grants on acceptance. Null if the role no longer exists."
    )  # type: ignore[misc]
    def role(
        self,
    ) -> (
        Annotated[
            RoleGQL,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.role"),
        ]
        | None
    ):
        return None


# -- Connection --

RoleInvitationEdge = Edge[RoleInvitationGQL]


@gql_connection_type(_meta("Role invitation connection."))
class RoleInvitationConnection(Connection[RoleInvitationGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count

    @classmethod
    def empty(cls) -> Self:
        return cls(
            edges=[],
            page_info=strawberry.relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
            count=0,
        )


# -- OrderBy --


@gql_pydantic_input(
    _meta("Order by specification for role invitations."), name="RoleInvitationOrderBy"
)
class RoleInvitationOrderByGQL(PydanticInputMixin[Any], GQLOrderBy):
    field: RoleInvitationOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC


# -- Filters --


@gql_pydantic_input(_meta("Filter for role invitation state."), name="RoleInvitationStateFilter")
class RoleInvitationStateFilterGQL(PydanticInputMixin[Any]):
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
    _meta("Nested filter for the role associated with an invitation."),
    name="RoleInvitationRoleNestedFilter",
)
class RoleInvitationRoleNestedFilterGQL(PydanticInputMixin[Any]):
    name: StringFilter | None = None


@gql_pydantic_input(
    _meta("Nested filter for a user (inviter or invitee) of an invitation."),
    name="RoleInvitationUserNestedFilter",
)
class RoleInvitationUserNestedFilterGQL(PydanticInputMixin[Any]):
    email: StringFilter | None = None


@gql_pydantic_input(_meta("Filter for role invitations."), name="RoleInvitationFilter")
class RoleInvitationFilterGQL(PydanticInputMixin[Any], GQLFilter):
    state: RoleInvitationStateFilterGQL | None = None
    role_id: UUIDFilter | None = None
    role: RoleInvitationRoleNestedFilterGQL | None = None
    inviter: RoleInvitationUserNestedFilterGQL | None = None
    invitee: RoleInvitationUserNestedFilterGQL | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


# -- Inputs --


@gql_pydantic_input(_meta("Input for creating role invitations."), name="CreateRoleInvitationInput")
class CreateRoleInvitationInputGQL(PydanticInputMixin[Any]):
    role_id: UUID
    emails: list[str]


@gql_pydantic_input(
    _meta("Input for accepting a role invitation."), name="AcceptRoleInvitationInput"
)
class AcceptRoleInvitationInputGQL(PydanticInputMixin[Any]):
    invitation_id: UUID


@gql_pydantic_input(
    _meta("Input for rejecting a role invitation."), name="RejectRoleInvitationInput"
)
class RejectRoleInvitationInputGQL(PydanticInputMixin[Any]):
    invitation_id: UUID


@gql_pydantic_input(
    _meta("Input for canceling a role invitation."), name="CancelRoleInvitationInput"
)
class CancelRoleInvitationInputGQL(PydanticInputMixin[Any]):
    invitation_id: UUID


# -- Payloads --


@gql_pydantic_type(
    _meta("Payload for role invitation creation."),
    model=CreateRoleInvitationPayloadDTO,
    name="CreateRoleInvitationPayload",
)
class CreateRoleInvitationPayloadGQL(PydanticOutputMixin[CreateRoleInvitationPayloadDTO]):
    items: list[RoleInvitationGQL] = gql_field(description="List of created role invitations.")
