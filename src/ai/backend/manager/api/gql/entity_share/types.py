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
from ai.backend.common.dto.manager.v2.entity_share.request import (
    MySearchEntitySharesInput as MySearchInputDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntityShareNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntitySharePayload as PayloadDTO,
)
from ai.backend.common.dto.manager.v2.entity_share.types import (
    EntityShareSideDTO,
    EntityShareStatusDTO,
)
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
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Where a share stands."),
    EntityShareStatusDTO,
    name="EntityShareStatus",
)

EntityShareSideGQL: type[EntityShareSideDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Which side of a share the caller stands on.",
    ),
    EntityShareSideDTO,
    name="EntityShareSide",
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
        added_version=NEXT_RELEASE_VERSION, description="Order fields for entity shares."
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
        description="One entity handed to one scope: offered, taken, or taken back.",
    ),
    name="EntityShare",
)
class EntityShareGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    sharer_user_id: UUID = gql_field(description="Who sent the offer.")
    recipient_entity_type: str | None = gql_field(
        default=None, description="Type of the scope the offer goes to, once it names one."
    )
    recipient_entity_id: UUID | None = gql_field(
        default=None, description="Id of the scope the offer goes to, once it names one."
    )
    recipient_email: str | None = gql_field(
        default=None, description="Address the offer goes to, when it names one."
    )
    target_entity_type: str = gql_field(description="Type of the entity being offered.")
    target_entity_id: UUID = gql_field(description="Id of the entity being offered.")
    permissions: list[PermissionBitGQL] = gql_field(
        description="Permissions the offer caps at; empty for no ceiling."
    )
    status: EntityShareStatusGQL = gql_field(description="Where the share stands.")
    expires_at: datetime | None = gql_field(
        default=None, description="When the offer stops being answerable; empty for never."
    )
    created_at: datetime = gql_field(description="When the offer was made.")
    updated_at: datetime = gql_field(description="When it was last written.")


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="One entity share within a connection."
    )
)
class EntityShareEdge(Edge[EntityShareGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Paginated list of entity shares."
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
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Filter for entity shares."),
    name="EntityShareFilter",
)
class EntityShareFilterGQL(PydanticInputMixin[FilterDTO]):
    status: EntityShareStatusGQL | None = gql_field(default=None, description="Status filter.")
    recipient_entity_id: UUID | None = gql_field(
        default=None, description="Exact recipient scope match."
    )
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
        description="One entity whose shares are being read.",
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
            "Scope for the scoped entity share query. "
            "All items are OR'd; raises an error if every field is empty."
        ),
    ),
    name="EntityShareScope",
)
class EntityShareScopeGQL(PydanticInputMixin[ScopeDTO]):
    recipient: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users the shares are addressed to."
    )
    recipient_project: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Projects the shares are addressed to."
    )
    sharer: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users who sent the shares."
    )
    target: list[EntityShareTargetScopeGQL] | None = gql_field(
        default=None, description="Entities the shares lend."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create entity share input; names exactly one recipient.",
    ),
    name="CreateEntityShareInput",
)
class CreateEntityShareInputGQL(PydanticInputMixin[CreateInputDTO]):
    target_entity_type: str = gql_field(description="Type of the entity being offered.")
    target_entity_id: UUID = gql_field(description="Id of the entity being offered.")
    recipient_project_id: UUID | None = gql_field(
        default=None, description="Project the offer goes to."
    )
    recipient_user_id: UUID | None = gql_field(
        default=None, description="Person the offer goes to; it lands in their own project."
    )
    recipient_email: str | None = gql_field(default=None, description="Address the offer goes to.")
    permissions: list[PermissionBitGQL] = gql_field(
        default=(), description="Permissions the offer caps at; empty for no ceiling."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Entity share payload."),
    model=PayloadDTO,
    name="EntitySharePayload",
)
class EntitySharePayloadGQL(PydanticOutputMixin[PayloadDTO]):
    share: EntityShareGQL = gql_field(description="The share the run touched.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Read the shares the caller stands on a side of.",
    ),
    name="MySearchEntitySharesInput",
)
class MySearchEntitySharesInputGQL(PydanticInputMixin[MySearchInputDTO]):
    sides: list[EntityShareSideGQL] = gql_field(
        default=(), description="Sides the caller stands on; empty for both."
    )
