"""VFolderV2 GraphQL query resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder_v2.types import (
    VFolderV2Connection,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List virtual folders within a specific project.",
    )
)  # type: ignore[misc]
async def project_vfolders_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFolderV2Connection:
    """List virtual folders within a specific project."""
    # Stub: returns empty connection until adapter is wired.
    return VFolderV2Connection(
        edges=[],
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        ),
        count=0,
    )
