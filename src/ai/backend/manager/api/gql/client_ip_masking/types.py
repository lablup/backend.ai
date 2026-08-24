from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminUpsertClientIPMaskingPolicyInput as UpsertInputDTO,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    ClientIPMaskingPolicyFilter as FilterDTO,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    ClientIPMaskingPolicyOrder as OrderDTO,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.response import (
    ClientIPMaskingPolicyNode as NodeDTO,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.response import (
    ClientIPMaskingPolicyPayload as PolicyPayloadDTO,
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
        description="Which recorded client IP a masking policy governs.",
    ),
    name="ClientIPMaskingTarget",
)
class ClientIPMaskingTargetGQL(StrEnum):
    DEFAULT = "default"
    LOGIN_HISTORY = "login_history"
    AUDIT_LOGS = "audit_logs"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Masking applied before a client IP is stored. 'none' keeps the address as "
            "observed, 'truncate' zeroes the host bits — keeping an IPv4 /24 and an "
            "IPv6 /48 — and 'drop' records no address at all."
        ),
    ),
    name="ClientIPMaskingMode",
)
class ClientIPMaskingModeGQL(StrEnum):
    NONE = "none"
    TRUNCATE = "truncate"
    DROP = "drop"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Order fields for client IP masking policies.",
    ),
    name="ClientIPMaskingPolicyOrderField",
)
class ClientIPMaskingPolicyOrderFieldGQL(StrEnum):
    TARGET_TYPE = "target_type"
    MODE = "mode"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "The masking one target gets. A target with no policy falls back to the "
            "'default' target, and no default means the address is recorded as observed."
        ),
    ),
    name="ClientIPMaskingPolicy",
)
class ClientIPMaskingPolicyGQL(PydanticNodeMixin[NodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    target_type: ClientIPMaskingTargetGQL = gql_field(
        description="Which recorded client IP is governed."
    )
    mode: ClientIPMaskingModeGQL = gql_field(
        description="Masking applied before the address is stored."
    )
    ipv4_prefix: int | None = gql_field(
        description="IPv4 bits 'truncate' keeps; null takes the built-in width of 24."
    )
    ipv6_prefix: int | None = gql_field(
        description="IPv6 bits 'truncate' keeps; null takes the built-in width of 48."
    )
    created_at: datetime = gql_field(description="Timestamp when the policy was first written.")
    updated_at: datetime = gql_field(description="Timestamp when the policy was last changed.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Set the masking one target gets, replacing the policy it already has.",
    ),
    name="UpsertClientIPMaskingPolicyInput",
)
class UpsertClientIPMaskingPolicyInputGQL(PydanticInputMixin[UpsertInputDTO]):
    target_type: ClientIPMaskingTargetGQL = gql_field(
        description="Which recorded client IP to govern."
    )
    mode: ClientIPMaskingModeGQL = gql_field(
        description="Masking applied before the address is stored."
    )
    ipv4_prefix: int | None = gql_field(
        default=None,
        description="IPv4 bits 'truncate' keeps; null takes the built-in width of 24.",
    )
    ipv6_prefix: int | None = gql_field(
        default=None,
        description="IPv6 bits 'truncate' keeps; null takes the built-in width of 48.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload carrying the settled client IP masking policy.",
    ),
    model=PolicyPayloadDTO,
    name="ClientIPMaskingPolicyPayload",
)
class ClientIPMaskingPolicyPayloadGQL(PydanticOutputMixin[PolicyPayloadDTO]):
    policy: ClientIPMaskingPolicyGQL = gql_field(description="The policy the operation left.")


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="An edge of the client IP masking policy connection.",
    ),
    name="ClientIPMaskingPolicyEdge",
)
class ClientIPMaskingPolicyEdgeGQL(Edge[ClientIPMaskingPolicyGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated list of client IP masking policies.",
    ),
    name="ClientIPMaskingPolicyConnection",
)
class ClientIPMaskingPolicyConnectionGQL(Connection[ClientIPMaskingPolicyGQL]):
    count: int = gql_field(description="Total number of policies matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for client IP masking policies.",
    ),
    name="ClientIPMaskingPolicyFilter",
)
class ClientIPMaskingPolicyFilterGQL(PydanticInputMixin[FilterDTO]):
    target_type: ClientIPMaskingTargetGQL | None = gql_field(
        default=None, description="Filter by the governed target."
    )
    mode: ClientIPMaskingModeGQL | None = gql_field(
        default=None, description="Filter by masking mode."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Order specification for client IP masking policies.",
    ),
    name="ClientIPMaskingPolicyOrderBy",
)
class ClientIPMaskingPolicyOrderByGQL(PydanticInputMixin[OrderDTO]):
    field: ClientIPMaskingPolicyOrderFieldGQL = gql_field(description="Field to order by.")
    direction: str = gql_field(default="ASC", description="ASC or DESC.")


__all__ = (
    "ClientIPMaskingModeGQL",
    "ClientIPMaskingPolicyConnectionGQL",
    "ClientIPMaskingPolicyEdgeGQL",
    "ClientIPMaskingPolicyFilterGQL",
    "ClientIPMaskingPolicyGQL",
    "ClientIPMaskingPolicyOrderByGQL",
    "ClientIPMaskingPolicyOrderFieldGQL",
    "ClientIPMaskingPolicyPayloadGQL",
    "ClientIPMaskingTargetGQL",
    "UpsertClientIPMaskingPolicyInputGQL",
)
