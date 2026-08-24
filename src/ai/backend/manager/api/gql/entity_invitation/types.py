from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    CreateEntityInvitationInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    EntityInvitationFilter as FilterDTO,
)
from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    EntityInvitationOrderBy as OrderByDTO,
)
from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    EntityInvitationScope as ScopeDTO,
)
from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    EntityInvitationTargetScope as TargetScopeDTO,
)
from ai.backend.common.dto.manager.v2.entity_invitation.response import (
    EntityInvitationNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.entity_invitation.response import (
    EntityInvitationPayload as PayloadDTO,
)
from ai.backend.common.dto.manager.v2.entity_invitation.types import EntityInvitationStatusDTO
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
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
from ai.backend.manager.api.gql.rbac.types.scope import UUIDScopeGQL

_ADDED = "26.8.3"

EntityInvitationStatusGQL: type[EntityInvitationStatusDTO] = gql_enum(
    BackendAIGQLMeta(added_version=_ADDED, description="Whether an invitation is still open."),
    EntityInvitationStatusDTO,
    name="EntityInvitationStatus",
)

PermissionBitGQL: type[PermissionBitDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=_ADDED,
        description="One bit of a permission mask; distinct from OperationType, which names an action.",
    ),
    PermissionBitDTO,
    name="PermissionBit",
)


@gql_enum(
    BackendAIGQLMeta(added_version=_ADDED, description="Order fields for entity invitations."),
    name="EntityInvitationOrderField",
)
class EntityInvitationOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"


@gql_node_type(
    BackendAIGQLMeta(
        added_version=_ADDED,
        description="An offer of one existing entity to one address, settled by the answer.",
    ),
    name="EntityInvitation",
)
class EntityInvitationGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    inviter_user_id: UUID = gql_field(description="Who sent the offer.")
    invitee_email: str = gql_field(description="Address the offer goes to.")
    target_entity_type: str = gql_field(description="Type of the entity being offered.")
    target_entity_id: UUID = gql_field(description="Id of the entity being offered.")
    permissions: list[PermissionBitGQL] = gql_field(
        description="Permissions the offer caps at; empty for no ceiling."
    )
    status: EntityInvitationStatusGQL = gql_field(
        description="Whether the invitation is still open."
    )
    created_at: datetime = gql_field(description="When the offer was made.")
    updated_at: datetime = gql_field(description="When it was last written.")


EntityInvitationEdge = Edge[EntityInvitationGQL]


@gql_connection_type(
    BackendAIGQLMeta(added_version=_ADDED, description="Paginated list of entity invitations.")
)
class EntityInvitationConnection(Connection[EntityInvitationGQL]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=_ADDED, description="Filter for entity invitations."),
    name="EntityInvitationFilter",
)
class EntityInvitationFilterGQL(PydanticInputMixin[FilterDTO]):
    status: EntityInvitationStatusGQL | None = gql_field(default=None, description="Status filter.")
    invitee_email: str | None = gql_field(default=None, description="Exact address match.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=_ADDED, description="Order specification."),
    name="EntityInvitationOrderBy",
)
class EntityInvitationOrderByGQL(PydanticInputMixin[OrderByDTO]):
    field: EntityInvitationOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="DESC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=_ADDED, description="One entity whose invitations are being read."
    ),
    name="EntityInvitationTargetScope",
)
class EntityInvitationTargetScopeGQL(PydanticInputMixin[TargetScopeDTO]):
    entity_type: str = gql_field(description="Type of the entity being offered.")
    entity_id: UUID = gql_field(description="Id of the entity being offered.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=_ADDED,
        description=(
            "Scope for the scoped entity invitation query. "
            "All items are OR'd; raises an error if every field is empty."
        ),
    ),
    name="EntityInvitationScope",
)
class EntityInvitationScopeGQL(PydanticInputMixin[ScopeDTO]):
    invitee: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users the invitations are addressed to."
    )
    inviter: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users who sent the invitations."
    )
    target: list[EntityInvitationTargetScopeGQL] | None = gql_field(
        default=None, description="Entities the invitations offer."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=_ADDED, description="Create entity invitation input."),
    name="CreateEntityInvitationInput",
)
class CreateEntityInvitationInputGQL(PydanticInputMixin[CreateInputDTO]):
    target_entity_type: str = gql_field(description="Type of the entity being offered.")
    target_entity_id: UUID = gql_field(description="Id of the entity being offered.")
    invitee_email: str = gql_field(description="Address the offer goes to.")
    permissions: list[PermissionBitGQL] = gql_field(
        default=(), description="Permissions the offer caps at; empty for no ceiling."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=_ADDED, description="Entity invitation payload."),
    model=PayloadDTO,
    name="EntityInvitationPayload",
)
class EntityInvitationPayloadGQL(PydanticOutputMixin[PayloadDTO]):
    invitation: EntityInvitationGQL = gql_field(description="The invitation the run touched.")
