from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.entity_share.request import (
    CreateEntityShareInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.request import (
    EntityShareFilter as FilterDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.request import (
    EntityShareOrderBy as OrderByDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.request import (
    EntityShareScope as ScopeDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.request import (
    EntityShareTargetScope as TargetScopeDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntityShareNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntitySharePayload as PayloadDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareStatusDTO
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
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
from ai.backend.manager.api.gql.rbac.types.scope import UUIDScopeGQL

EntityShareStatusGQL: type[EntityShareStatusDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Whether an invitation is still open."
    ),
    EntityShareStatusDTO,
    name="EntityShareStatus",
)

PermissionBitGQL: type[PermissionBitDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One bit of a permission mask; distinct from OperationType, which names an action.",
    ),
    PermissionBitDTO,
    name="PermissionBit",
)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Order fields for entity invitations."
    ),
    name="EntityShareOrderField",
)
class EntityShareOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="An offer of one existing entity to one address, settled by the answer.",
    ),
    name="EntityShare",
)
class EntityShareGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    sharer_user_id: UUID = gql_field(description="Who sent the offer.")
    recipient_email: str = gql_field(description="Address the offer goes to.")
    target_entity_type: str = gql_field(description="Type of the entity being offered.")
    target_entity_id: UUID = gql_field(description="Id of the entity being offered.")
    permissions: list[PermissionBitGQL] = gql_field(
        description="Permissions the offer caps at; empty for no ceiling."
    )
    status: EntityShareStatusGQL = gql_field(description="Whether the invitation is still open.")
    created_at: datetime = gql_field(description="When the offer was made.")
    updated_at: datetime = gql_field(description="When it was last written.")


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="One entity invitation within a connection."
    )
)
class EntityShareEdge(Edge[EntityShareGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Paginated list of entity invitations."
    )
)
class EntityShareConnection(Connection[EntityShareGQL]):
    # Restated so the schema's edge type is the described one above rather than the
    # one Strawberry would generate from the generic, which carries no version.
    edges: list[EntityShareEdge] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Filter for entity invitations."
    ),
    name="EntityShareFilter",
)
class EntityShareFilterGQL(PydanticInputMixin[FilterDTO]):
    status: EntityShareStatusGQL | None = gql_field(default=None, description="Status filter.")
    recipient_email: str | None = gql_field(default=None, description="Exact address match.")


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Order specification."),
    name="EntityShareOrderBy",
)
class EntityShareOrderByGQL(PydanticInputMixin[OrderByDTO]):
    field: EntityShareOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="DESC", description="ASC or DESC.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One entity whose invitations are being read.",
    ),
    name="EntityShareTargetScope",
)
class EntityShareTargetScopeGQL(PydanticInputMixin[TargetScopeDTO]):
    entity_type: str = gql_field(description="Type of the entity being offered.")
    entity_id: UUID = gql_field(description="Id of the entity being offered.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Scope for the scoped entity invitation query. "
            "All items are OR'd; raises an error if every field is empty."
        ),
    ),
    name="EntityShareScope",
)
class EntityShareScopeGQL(PydanticInputMixin[ScopeDTO]):
    invitee: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users the invitations are addressed to."
    )
    inviter: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users who sent the invitations."
    )
    target: list[EntityShareTargetScopeGQL] | None = gql_field(
        default=None, description="Entities the invitations offer."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Create entity invitation input."
    ),
    name="CreateEntityShareInput",
)
class CreateEntityShareInputGQL(PydanticInputMixin[CreateInputDTO]):
    target_entity_type: str = gql_field(description="Type of the entity being offered.")
    target_entity_id: UUID = gql_field(description="Id of the entity being offered.")
    recipient_email: str = gql_field(description="Address the offer goes to.")
    permissions: list[PermissionBitGQL] = gql_field(
        default=(), description="Permissions the offer caps at; empty for no ceiling."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Entity invitation payload."),
    model=PayloadDTO,
    name="EntitySharePayload",
)
class EntitySharePayloadGQL(PydanticOutputMixin[PayloadDTO]):
    invitation: EntityShareGQL = gql_field(description="The invitation the run touched.")
