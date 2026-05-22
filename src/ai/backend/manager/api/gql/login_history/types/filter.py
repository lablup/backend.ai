"""LoginHistory GraphQL filter types."""

from __future__ import annotations

from typing import Self

from ai.backend.common.dto.manager.v2.login_history.request import (
    LoginHistoryFilter,
    LoginHistoryResultFilter,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

from .node import LoginAttemptResultGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for login attempt result field.",
        added_version="26.4.2",
    ),
    name="LoginHistoryResultFilter",
)
class LoginHistoryResultFilterGQL(PydanticInputMixin[LoginHistoryResultFilter]):
    equals: LoginAttemptResultGQL | None = None
    in_: list[LoginAttemptResultGQL] | None = gql_field(
        description="The in field.", name="in", default=None
    )
    not_equals: LoginAttemptResultGQL | None = gql_field(
        description="Excludes exact result match.", name="notEquals", default=None
    )
    not_in: list[LoginAttemptResultGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying login history.",
        added_version="26.4.2",
    ),
    name="LoginHistoryFilter",
)
class LoginHistoryFilterGQL(PydanticInputMixin[LoginHistoryFilter]):
    domain_name: StringFilter | None = None
    result: LoginHistoryResultFilterGQL | None = None
    created_at: DateTimeFilter | None = None
    client_ip: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by the client IP recorded on the login_history event.",
        ),
        default=None,
    )

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None
