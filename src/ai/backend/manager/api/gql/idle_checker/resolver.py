from __future__ import annotations

from uuid import UUID

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
    IdleCheckerOrderGQL,
    PurgeIdleCheckerPayloadGQL,
    UpdateIdleCheckerInputGQL,
    UpdateIdleCheckerPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.errors.api import NotImplementedAPI


async def admin_idle_checkers(
    info: Info[StrawberryGQLContext],
    filter: IdleCheckerFilterGQL | None = None,
    order_by: list[IdleCheckerOrderGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> IdleCheckerConnectionGQL:
    check_admin_only()
    raise NotImplementedAPI("Idle checker search is not implemented.")


admin_idle_checkers = gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Searches all registered idle checkers with filtering, ordering, and pagination. "
            "Only superadministrators can access this global collection."
        ),
    )
)(admin_idle_checkers)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Registers a new idle checker using a supported typed specification. "
            "Only superadministrators can perform this global operation."
        ),
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
        description=(
            "Updates selected fields of an existing idle checker. "
            "Only superadministrators can modify these global definitions."
        ),
    )
)
async def admin_update_idle_checker(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateIdleCheckerInputGQL,
) -> UpdateIdleCheckerPayloadGQL:
    check_admin_only()
    raise NotImplementedAPI("Idle checker update is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Permanently removes an idle checker and returns its identifier. "
            "Only superadministrators can perform this irreversible global operation."
        ),
    )
)
async def admin_purge_idle_checker(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeIdleCheckerPayloadGQL:
    check_admin_only()
    raise NotImplementedAPI("Idle checker purge is not implemented.")
