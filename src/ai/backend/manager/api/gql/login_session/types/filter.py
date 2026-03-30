"""LoginSession GraphQL filter types."""

from __future__ import annotations

from typing import Self

from ai.backend.common.dto.manager.v2.login_session.request import (
    LoginSessionFilter,
    LoginSessionStatusFilter,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

from .node import LoginSessionStatusGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for login session status field.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="LoginSessionStatusFilter",
)
class LoginSessionStatusFilterGQL(PydanticInputMixin[LoginSessionStatusFilter]):
    equals: LoginSessionStatusGQL | None = None
    in_: list[LoginSessionStatusGQL] | None = gql_field(
        description="The in field.", name="in", default=None
    )
    not_in: list[LoginSessionStatusGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter criteria for querying login sessions.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="LoginSessionFilter",
)
class LoginSessionFilterGQL(PydanticInputMixin[LoginSessionFilter]):
    status: LoginSessionStatusFilterGQL | None = None
    access_key: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    last_accessed_at: DateTimeFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None
