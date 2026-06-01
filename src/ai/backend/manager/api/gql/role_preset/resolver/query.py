"""Role preset GQL query resolvers.

Function bodies raise ``NotImplementedError``; wire-up to the adapter/service
layer happens in a follow-up task.
"""

from __future__ import annotations

from strawberry import ID, Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.role_preset.types import (
    RolePresetConnection,
    RolePresetFilterGQL,
    RolePresetGQL,
    RolePresetOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single role preset by ID (admin only).",
    )
)  # type: ignore[misc]
async def admin_role_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> RolePresetGQL | None:
    check_admin_only()
    raise NotImplementedError


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List role presets with filtering and pagination (admin only).",
    )
)  # type: ignore[misc]
async def admin_role_presets(
    info: Info[StrawberryGQLContext],
    filter: RolePresetFilterGQL | None = None,
    order_by: list[RolePresetOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RolePresetConnection | None:
    check_admin_only()
    raise NotImplementedError
