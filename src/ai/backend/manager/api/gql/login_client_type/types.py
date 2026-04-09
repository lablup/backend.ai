"""GraphQL types for login client type."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.login_client_type.request import (
    CreateLoginClientTypeInput as CreateLoginClientTypeInputDTO,
)
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    LoginClientTypeFilter as LoginClientTypeFilterDTO,
)
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    LoginClientTypeOrder as LoginClientTypeOrderDTO,
)
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    UpdateLoginClientTypeInput as UpdateLoginClientTypeInputDTO,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    CreateLoginClientTypePayload as CreateLoginClientTypePayloadDTO,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    DeleteLoginClientTypePayload as DeleteLoginClientTypePayloadDTO,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    LoginClientTypeNode,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    UpdateLoginClientTypePayload as UpdateLoginClientTypePayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
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

__all__ = (
    "CreateLoginClientTypeInputGQL",
    "CreateLoginClientTypePayloadGQL",
    "DeleteLoginClientTypePayloadGQL",
    "LoginClientTypeConnection",
    "LoginClientTypeEdge",
    "LoginClientTypeFilterGQL",
    "LoginClientTypeGQL",
    "LoginClientTypeOrderByGQL",
    "LoginClientTypeOrderFieldGQL",
    "UpdateLoginClientTypeInputGQL",
    "UpdateLoginClientTypePayloadGQL",
)


# ---------------------------------------------------------------------------
# Node / Edge / Connection
# ---------------------------------------------------------------------------


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A registered login client type that the auth flow can attribute sessions to.",
    ),
    name="LoginClientType",
)
class LoginClientTypeGQL(PydanticNodeMixin[LoginClientTypeNode]):
    id: NodeID[str] = gql_field(
        description="Relay-style global node identifier for the login client type."
    )
    name: str = gql_field(description="Unique login client type name (e.g. 'core', 'webui').")
    description: str | None = gql_field(description="Optional administrator-facing description.")


LoginClientTypeEdge = Edge[LoginClientTypeGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for login client type records.",
    ),
)
class LoginClientTypeConnection(Connection[LoginClientTypeGQL]):
    count: int = gql_field(
        description="Total number of login client type records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ---------------------------------------------------------------------------
# Filter / OrderBy
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying login client types.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="LoginClientTypeFilter",
)
class LoginClientTypeFilterGQL(PydanticInputMixin[LoginClientTypeFilterDTO]):
    name: StringFilter | None = gql_field(description="Filter by name.", default=None)
    description: StringFilter | None = gql_field(description="Filter by description.", default=None)
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by creation datetime.", default=None
    )
    modified_at: DateTimeFilter | None = gql_field(
        description="Filter by last modification datetime.", default=None
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering login client type results.",
    ),
    name="LoginClientTypeOrderField",
)
class LoginClientTypeOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for login client type results.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="LoginClientTypeOrderBy",
)
class LoginClientTypeOrderByGQL(PydanticInputMixin[LoginClientTypeOrderDTO]):
    field: LoginClientTypeOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(
        description="Sort direction.", default=OrderDirection.DESC
    )


# ---------------------------------------------------------------------------
# Mutation inputs / payloads
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a new login client type.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="CreateLoginClientTypeInput",
)
class CreateLoginClientTypeInputGQL(PydanticInputMixin[CreateLoginClientTypeInputDTO]):
    name: str = gql_field(description="Unique login client type name.")
    description: str | None = gql_field(
        default=None, description="Optional description shown to administrators."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for login client type creation.",
    ),
    model=CreateLoginClientTypePayloadDTO,
    name="CreateLoginClientTypePayload",
)
class CreateLoginClientTypePayloadGQL(PydanticOutputMixin[CreateLoginClientTypePayloadDTO]):
    login_client_type: LoginClientTypeGQL = gql_field(description="The created login client type.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Input for updating a login client type. Both fields are optional for partial update."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="UpdateLoginClientTypeInput",
)
class UpdateLoginClientTypeInputGQL(PydanticInputMixin[UpdateLoginClientTypeInputDTO]):
    name: str | None = gql_field(default=None, description="Updated name.")
    description: str | None = gql_field(
        default=None,
        description="Updated description. Pass null to clear, omit to leave unchanged.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for login client type update.",
    ),
    model=UpdateLoginClientTypePayloadDTO,
    name="UpdateLoginClientTypePayload",
)
class UpdateLoginClientTypePayloadGQL(PydanticOutputMixin[UpdateLoginClientTypePayloadDTO]):
    login_client_type: LoginClientTypeGQL = gql_field(description="The updated login client type.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for login client type deletion.",
    ),
    model=DeleteLoginClientTypePayloadDTO,
    name="DeleteLoginClientTypePayload",
)
class DeleteLoginClientTypePayloadGQL(PydanticOutputMixin[DeleteLoginClientTypePayloadDTO]):
    id: str = gql_field(description="UUID of the deleted login client type.")
