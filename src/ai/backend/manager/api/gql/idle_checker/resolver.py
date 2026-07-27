from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.idle_checker.types import (
    CreateIdleCheckerInputGQL,
    CreateIdleCheckerPayloadGQL,
    IdleCheckerConnectionGQL,
    IdleCheckerFilterGQL,
    IdleCheckerOrderByGQL,
    PurgeIdleCheckerInputGQL,
    PurgeIdleCheckerPayloadGQL,
    UpdateIdleCheckerInputGQL,
    UpdateIdleCheckerPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.errors.api import NotImplementedAPI


@gql_root_field(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Searches global idle checker definitions with filtering, ordering, and "
            "pagination (super admin only)."
        ),
    )
)
async def admin_idle_checkers(
    info: Info[StrawberryGQLContext],
    filter: IdleCheckerFilterGQL | None = None,
    order_by: list[IdleCheckerOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> IdleCheckerConnectionGQL:
    check_admin_only()
    raise NotImplementedAPI("Idle checker search is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Creates a global idle checker definition (super admin only).",
    )
)
async def admin_create_idle_checker(
    info: Info[StrawberryGQLContext],
    input: CreateIdleCheckerInputGQL,
) -> CreateIdleCheckerPayloadGQL:
    check_admin_only()
    raise NotImplementedAPI("Idle checker creation is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Updates a global idle checker definition (super admin only).",
    )
)
async def admin_update_idle_checker(
    info: Info[StrawberryGQLContext],
    input: UpdateIdleCheckerInputGQL,
) -> UpdateIdleCheckerPayloadGQL:
    check_admin_only()
    raise NotImplementedAPI("Idle checker update is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently removes an unbound idle checker (super admin only).",
    )
)
async def admin_purge_idle_checker(
    info: Info[StrawberryGQLContext],
    input: PurgeIdleCheckerInputGQL,
) -> PurgeIdleCheckerPayloadGQL:
    check_admin_only()
    raise NotImplementedAPI("Idle checker purge is not implemented.")
