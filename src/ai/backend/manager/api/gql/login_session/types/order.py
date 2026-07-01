"""LoginSession GraphQL order types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.login_session.request import LoginSessionOrder
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Fields available for ordering login sessions.",
    ),
    name="LoginSessionOrderField",
)
class LoginSessionOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    STATUS = "status"
    LAST_ACCESSED_AT = "last_accessed_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Ordering specification for login sessions.",
        added_version="26.4.2",
    ),
    name="LoginSessionOrderBy",
)
class LoginSessionOrderByGQL(PydanticInputMixin[LoginSessionOrder]):
    field: LoginSessionOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC
