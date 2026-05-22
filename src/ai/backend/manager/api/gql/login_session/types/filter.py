"""LoginSession GraphQL filter types."""

from __future__ import annotations

from typing import Self

from ai.backend.common.dto.manager.v2.login_session.request import (
    LoginSessionFilter,
    LoginSessionStatusFilter,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

from .node import LoginSessionStatusGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for login session status field.",
        added_version="26.4.2",
    ),
    name="LoginSessionStatusFilter",
)
class LoginSessionStatusFilterGQL(PydanticInputMixin[LoginSessionStatusFilter]):
    equals: LoginSessionStatusGQL | None = None
    in_: list[LoginSessionStatusGQL] | None = gql_field(
        description="The in field.", name="in", default=None
    )
    not_equals: LoginSessionStatusGQL | None = gql_field(
        description="Excludes exact status match.", name="notEquals", default=None
    )
    not_in: list[LoginSessionStatusGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying login sessions.",
        added_version="26.4.2",
    ),
    name="LoginSessionFilter",
)
class LoginSessionFilterGQL(PydanticInputMixin[LoginSessionFilter]):
    user_id: UUIDFilter | None = None
    status: LoginSessionStatusFilterGQL | None = None
    access_key: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    last_accessed_at: DateTimeFilter | None = None
    client_ip: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by the originating client IP recorded on the session.",
        ),
        default=None,
    )

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None
