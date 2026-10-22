"""Session group GraphQL types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self, cast, override
from uuid import UUID

import strawberry
from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.dto.manager.v2.session_group.request import (
    PurgeSessionGroupInput as PurgeSessionGroupInputDTO,
)
from ai.backend.common.dto.manager.v2.session_group.request import (
    SessionGroupFilter as SessionGroupFilterDTO,
)
from ai.backend.common.dto.manager.v2.session_group.request import (
    SessionGroupOrder as SessionGroupOrderDTO,
)
from ai.backend.common.dto.manager.v2.session_group.request import (
    SessionGroupPlacementDirectionFilter as SessionGroupPlacementDirectionFilterDTO,
)
from ai.backend.common.dto.manager.v2.session_group.request import (
    SessionGroupPlacementEnforcementFilter as SessionGroupPlacementEnforcementFilterDTO,
)
from ai.backend.common.dto.manager.v2.session_group.request import (
    UpdateSessionGroupInput as UpdateSessionGroupInputDTO,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    PurgeSessionGroupPayload as PurgeSessionGroupPayloadDTO,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    SessionGroupNode as SessionGroupNodeDTO,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    UpdateSessionGroupPayload as UpdateSessionGroupPayloadDTO,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupOrderField as SessionGroupOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum as SessionGroupPlacementDirectionDTO,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementEnforcementEnum as SessionGroupPlacementEnforcementDTO,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupScope as SessionGroupScopeDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    NullableDateTimeFilter,
    OrderDirection,
    UUIDFilter,
    UUIDScopeGQL,
)
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
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "PurgeSessionGroupInputGQL",
    "PurgeSessionGroupPayloadGQL",
    "SessionGroupConnectionGQL",
    "SessionGroupEdgeGQL",
    "SessionGroupFilterGQL",
    "SessionGroupGQL",
    "SessionGroupOrderByGQL",
    "SessionGroupScopeGQL",
    "UpdateSessionGroupInputGQL",
    "UpdateSessionGroupPayloadGQL",
)


SessionGroupPlacementDirectionGQL: type[SessionGroupPlacementDirectionDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="How the member sessions of a group sit relative to each other, per agent.",
    ),
    SessionGroupPlacementDirectionDTO,
    name="SessionGroupPlacementDirection",
)

SessionGroupPlacementEnforcementGQL: type[SessionGroupPlacementEnforcementDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="How hard the placement direction is enforced when it cannot be satisfied.",
    ),
    SessionGroupPlacementEnforcementDTO,
    name="SessionGroupPlacementEnforcement",
)

SessionGroupOrderFieldGQL: type[SessionGroupOrderFieldDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering session groups.",
    ),
    SessionGroupOrderFieldDTO,
    name="SessionGroupOrderField",
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A set of sessions sharing a placement policy. The group belongs to a project "
            "and is owned by one user."
        ),
    ),
    name="SessionGroup",
)
class SessionGroupGQL(PydanticNodeMixin[SessionGroupNodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    entity_id: UUID = gql_field(description="ID of the session group.")
    domain_id: UUID = gql_field(description="ID of the domain the group belongs to.")
    project_id: UUID = gql_field(description="ID of the project the group belongs to.")
    owner_user_id: UUID = gql_field(
        description="ID of the user owning the group. Every member session belongs to this user."
    )
    placement_direction: SessionGroupPlacementDirectionGQL = gql_field(
        description="Whether member sessions are spread across agents or packed onto them."
    )
    placement_enforcement: SessionGroupPlacementEnforcementGQL = gql_field(
        description="Whether the direction is a preference or a hard constraint."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    deleted_at: datetime | None = gql_field(
        description="Deletion timestamp. Null while the group is in use."
    )

    @classmethod
    @override
    async def resolve_nodes(
        cls,
        *,
        info: Info[StrawberryGQLContext, Any],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self]:
        results = await info.context.data_loaders.session_group_loader.load_many([
            SessionGroupID(UUID(node_id)) for node_id in node_ids
        ])
        return cast(list[Self], results)


SessionGroupEdgeGQL = Edge[SessionGroupGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for session groups.",
    ),
    name="SessionGroupConnection",
)
class SessionGroupConnectionGQL(Connection[SessionGroupGQL]):
    count: int = gql_field(description="Total number of session groups matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the placement direction with equality and membership operators.",
    ),
    name="SessionGroupPlacementDirectionFilter",
)
class SessionGroupPlacementDirectionFilterGQL(
    PydanticInputMixin[SessionGroupPlacementDirectionFilterDTO]
):
    equals: SessionGroupPlacementDirectionGQL | None = gql_field(
        description="Exact match.", default=None
    )
    in_: list[SessionGroupPlacementDirectionGQL] | None = gql_field(
        description="Match any of the provided values.", name="in", default=None
    )
    not_equals: SessionGroupPlacementDirectionGQL | None = gql_field(
        description="Exclude an exact match.", default=None
    )
    not_in: list[SessionGroupPlacementDirectionGQL] | None = gql_field(
        description="Exclude any of the provided values.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the placement enforcement with equality and membership operators.",
    ),
    name="SessionGroupPlacementEnforcementFilter",
)
class SessionGroupPlacementEnforcementFilterGQL(
    PydanticInputMixin[SessionGroupPlacementEnforcementFilterDTO]
):
    equals: SessionGroupPlacementEnforcementGQL | None = gql_field(
        description="Exact match.", default=None
    )
    in_: list[SessionGroupPlacementEnforcementGQL] | None = gql_field(
        description="Match any of the provided values.", name="in", default=None
    )
    not_equals: SessionGroupPlacementEnforcementGQL | None = gql_field(
        description="Exclude an exact match.", default=None
    )
    not_in: list[SessionGroupPlacementEnforcementGQL] | None = gql_field(
        description="Exclude any of the provided values.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Filter for session groups. Groups marked deleted are left out unless the "
            "top-level filter gives `deletedAt`; one inside AND, OR or NOT does not lift that."
        ),
    ),
    name="SessionGroupFilter",
)
class SessionGroupFilterGQL(PydanticInputMixin[SessionGroupFilterDTO]):
    entity_id: UUIDFilter | None = gql_field(
        description="Filter by session group ID.", default=None
    )
    domain_id: UUIDFilter | None = gql_field(description="Filter by domain ID.", default=None)
    project_id: UUIDFilter | None = gql_field(description="Filter by project ID.", default=None)
    owner_user_id: UUIDFilter | None = gql_field(
        description="Filter by the ID of the owning user.", default=None
    )
    placement_direction: SessionGroupPlacementDirectionFilterGQL | None = gql_field(
        description="Filter by placement direction.", default=None
    )
    placement_enforcement: SessionGroupPlacementEnforcementFilterGQL | None = gql_field(
        description="Filter by placement enforcement.", default=None
    )
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by creation time.", default=None
    )
    deleted_at: NullableDateTimeFilter | None = gql_field(
        description=(
            "Filter by deletion time. Setting it on the top-level filter includes the groups "
            "marked deleted; inside AND, OR or NOT it does not."
        ),
        default=None,
    )
    AND: list[Self] | None = gql_field(description="Match all nested filters.", default=None)
    OR: list[Self] | None = gql_field(description="Match any nested filter.", default=None)
    NOT: list[Self] | None = gql_field(description="Negate nested filters.", default=None)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One ordering rule for a session group search.",
    ),
    name="SessionGroupOrderBy",
)
class SessionGroupOrderByGQL(PydanticInputMixin[SessionGroupOrderDTO]):
    field: SessionGroupOrderFieldGQL = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Scope for the scoped session group query. Each list is OR'd internally and "
            "across lists, and every scope named is authorized before the read runs."
        ),
    ),
    name="SessionGroupScope",
)
class SessionGroupScopeGQL(PydanticInputMixin[SessionGroupScopeDTO]):
    domain: list[UUIDScopeGQL] | None = gql_field(
        description="Domains whose session groups are being read.", default=None
    )
    project: list[UUIDScopeGQL] | None = gql_field(
        description="Projects whose session groups are being read.", default=None
    )
    user: list[UUIDScopeGQL] | None = gql_field(
        description="Users whose session groups are being read.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for changing a session group's placement policy. At least one of the two "
            "fields must be given; members placed afterwards follow the new policy."
        ),
    ),
    name="UpdateSessionGroupInput",
)
class UpdateSessionGroupInputGQL(PydanticInputMixin[UpdateSessionGroupInputDTO]):
    id: UUID = gql_field(description="ID of the session group to update.")
    placement_direction: SessionGroupPlacementDirectionGQL | None = gql_field(
        description="New placement direction. Omit to leave unchanged.", default=UNSET
    )
    placement_enforcement: SessionGroupPlacementEnforcementGQL | None = gql_field(
        description="New placement enforcement. Omit to leave unchanged.", default=UNSET
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Identifies the session group to purge.",
    ),
    name="PurgeSessionGroupInput",
)
class PurgeSessionGroupInputGQL(PydanticInputMixin[PurgeSessionGroupInputDTO]):
    id: UUID = gql_field(description="ID of the session group to purge.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a session group update.",
    ),
    model=UpdateSessionGroupPayloadDTO,
    name="UpdateSessionGroupPayload",
)
class UpdateSessionGroupPayloadGQL(PydanticOutputMixin[UpdateSessionGroupPayloadDTO]):
    session_group: SessionGroupGQL = gql_field(description="The updated session group.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Names the session group removed. Its member sessions remain.",
    ),
    model=PurgeSessionGroupPayloadDTO,
    name="PurgeSessionGroupPayload",
)
class PurgeSessionGroupPayloadGQL(PydanticOutputMixin[PurgeSessionGroupPayloadDTO]):
    purged_id: strawberry.ID = gql_field(description="Global ID of the purged session group.")
    entity_id: UUID = gql_field(description="UUID of the purged session group.")
