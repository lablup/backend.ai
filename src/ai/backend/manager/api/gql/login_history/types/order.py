"""LoginHistory GraphQL order types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.login_history.request import LoginHistoryOrder
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering login history.",
    ),
    name="LoginHistoryOrderField",
)
class LoginHistoryOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    RESULT = "result"
    DOMAIN_NAME = "domain_name"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Ordering specification for login history.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="LoginHistoryOrderBy",
)
class LoginHistoryOrderByGQL(PydanticInputMixin[LoginHistoryOrder]):
    field: LoginHistoryOrderFieldGQL
    direction: OrderDirection = OrderDirection.DESC
