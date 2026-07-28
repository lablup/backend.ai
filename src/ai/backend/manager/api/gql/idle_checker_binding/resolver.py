from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.idle_checker_binding.types import (
    CreateIdleCheckerBindingInputGQL,
    CreateIdleCheckerBindingPayloadGQL,
    IdleCheckerBindingConnectionGQL,
    IdleCheckerBindingFilterGQL,
    IdleCheckerBindingOrderByGQL,
    IdleCheckerBindingScopeGQL,
    PurgeIdleCheckerBindingInputGQL,
    PurgeIdleCheckerBindingPayloadGQL,
    UpdateIdleCheckerBindingInputGQL,
    UpdateIdleCheckerBindingPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.errors.api import NotImplementedAPI


@gql_root_field(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Searches idle checker bindings across all scopes with filtering, ordering, "
            "and pagination (super admin only)."
        ),
    )
)
async def admin_idle_checker_bindings(
    info: Info[StrawberryGQLContext],
    filter: IdleCheckerBindingFilterGQL | None = None,
    order_by: list[IdleCheckerBindingOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> IdleCheckerBindingConnectionGQL:
    check_admin_only()
    raise NotImplementedAPI("Idle checker binding search is not implemented.")


@gql_root_field(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Searches idle checker bindings within a single scope. "
            "Requires permission on the given scope (subject to RBAC)."
        ),
    )
)
async def scoped_idle_checker_bindings(
    info: Info[StrawberryGQLContext],
    scope: IdleCheckerBindingScopeGQL,
    filter: IdleCheckerBindingFilterGQL | None = None,
    order_by: list[IdleCheckerBindingOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> IdleCheckerBindingConnectionGQL:
    raise NotImplementedAPI("Scoped idle checker binding search is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Binds a global idle checker to a scope. "
            "Requires permission on the scope given in the input (subject to RBAC)."
        ),
    )
)
async def create_idle_checker_binding(
    info: Info[StrawberryGQLContext],
    input: CreateIdleCheckerBindingInputGQL,
) -> CreateIdleCheckerBindingPayloadGQL:
    raise NotImplementedAPI("Idle checker binding creation is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Updates an idle checker binding's options. "
            "Requires permission on the binding's scope (subject to RBAC)."
        ),
    )
)
async def update_idle_checker_binding(
    info: Info[StrawberryGQLContext],
    input: UpdateIdleCheckerBindingInputGQL,
) -> UpdateIdleCheckerBindingPayloadGQL:
    raise NotImplementedAPI("Idle checker binding update is not implemented.")


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Permanently removes an idle checker binding. "
            "Requires permission on the binding's scope (subject to RBAC)."
        ),
    )
)
async def purge_idle_checker_binding(
    info: Info[StrawberryGQLContext],
    input: PurgeIdleCheckerBindingInputGQL,
) -> PurgeIdleCheckerBindingPayloadGQL:
    raise NotImplementedAPI("Idle checker binding purge is not implemented.")
