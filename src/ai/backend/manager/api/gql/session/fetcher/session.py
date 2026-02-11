from __future__ import annotations

import sqlalchemy as sa
from strawberry import Info

from ai.backend.manager.api.gql.session.types import (
    SessionV2ConnectionGQL,
    SessionV2FilterGQL,
    SessionV2OrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


async def fetch_sessions(
    info: Info[StrawberryGQLContext],
    filter: SessionV2FilterGQL | None = None,
    order_by: list[SessionV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[sa.sql.expression.ColumnElement[bool]] | None = None,
) -> SessionV2ConnectionGQL:
    raise NotImplementedError
