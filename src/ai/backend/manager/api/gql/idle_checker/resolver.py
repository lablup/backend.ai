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
    IdleCheckerOrderByGQL,
    IdleCheckerScopeGQL,
    PurgeIdleCheckerPayloadGQL,
    UpdateIdleCheckerInputGQL,
    UpdateIdleCheckerPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.api import NotImplementedAPI


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Searches idle checkers available in the requested scope with filtering, "
            "ordering, and pagination."
        ),
    )
)  # type: ignore[misc]
async def scoped_idle_checkers(
    info: Info[StrawberryGQLContext],
    scope: IdleCheckerScopeGQL,
    filter: IdleCheckerFilterGQL | None = None,
    order_by: list[IdleCheckerOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> IdleCheckerConnectionGQL:
    raise NotImplementedAPI("Idle checker search is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Creates an idle checker and binds it to the requested management and "
            "application scope."
        ),
    )
)
async def create_idle_checker(
    info: Info[StrawberryGQLContext],
    scope: IdleCheckerScopeGQL,
    input: CreateIdleCheckerInputGQL,
) -> CreateIdleCheckerPayloadGQL:
    raise NotImplementedAPI("Idle checker creation is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Updates selected fields of an idle checker when the caller has management "
            "permission on that checker."
        ),
    )
)
async def update_idle_checker(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateIdleCheckerInputGQL,
) -> UpdateIdleCheckerPayloadGQL:
    raise NotImplementedAPI("Idle checker update is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Permanently removes an unbound idle checker when the caller has management "
            "permission on that checker."
        ),
    )
)
async def purge_idle_checker(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeIdleCheckerPayloadGQL:
    raise NotImplementedAPI("Idle checker purge is not implemented.")
