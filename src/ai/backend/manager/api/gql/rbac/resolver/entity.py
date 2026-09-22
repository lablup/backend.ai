"""Deprecated GQL resolver kept from the removed scope-entity association search."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.rbac.types.entity import (
    EntityConnection,
    EntityFilterGQL,
    EntityOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Search entity associations (admin only).",
        deprecated_version=NEXT_RELEASE_VERSION,
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. The scope-entity association is removed;"
        " this connection is always empty."
    ),
)  # type: ignore[misc]
async def admin_entities(
    info: Info[StrawberryGQLContext],
    filter: EntityFilterGQL | None = None,
    order_by: list[EntityOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityConnection | None:
    check_admin_only()
    return EntityConnection(
        edges=[],
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        ),
        count=0,
    )
