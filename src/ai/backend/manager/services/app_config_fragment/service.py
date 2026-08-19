from __future__ import annotations

from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
    AdminSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
    BulkPurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
    BulkUpsertAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
    PurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
    ScopedSearchAppConfigFragmentActionResult,
)

__all__ = ("AppConfigFragmentService",)


class AppConfigFragmentService:
    """Write/read paths for app config fragments (not admin-only).

    ``create`` is gated by the fragment's FK to ``app_config_allow_list``: an insert with
    no allow-list row for its ``(config_name, scope_type)`` is rejected as a write-not-
    allowed error. An allow-list row requires a registered ``config_name`` (FK), so this
    also enforces registration. An allow-listed user may therefore manage their own
    ``user``-scope fragment without admin privileges.
    """

    _repository: AppConfigFragmentRepository

    def __init__(self, repository: AppConfigFragmentRepository) -> None:
        self._repository = repository

    async def get(self, action: GetAppConfigFragmentAction) -> GetAppConfigFragmentActionResult:
        data = await self._repository.get_by_id(action.fragment_id)
        return GetAppConfigFragmentActionResult(fragment=data)

    async def bulk_upsert(
        self, action: BulkUpsertAppConfigFragmentsAction
    ) -> BulkUpsertAppConfigFragmentsActionResult:
        result = await self._repository.bulk_upsert(action.upserter_specs)
        return BulkUpsertAppConfigFragmentsActionResult(
            items=result.items, failed=result.failed, _scope=action.scope
        )

    async def admin_search(
        self, action: AdminSearchAppConfigFragmentAction
    ) -> AdminSearchAppConfigFragmentActionResult:
        result = await self._repository.admin_search(action.querier)
        return AdminSearchAppConfigFragmentActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def scoped_search(
        self, action: ScopedSearchAppConfigFragmentAction
    ) -> ScopedSearchAppConfigFragmentActionResult:
        # TODO(BA-7003): temporary single-scope search. The repository already OR-combines a
        # sequence of scopes, but ScopedSearchAppConfigFragmentAction is a single-scope
        # BaseScopeAction, so only one scope is passed here. BA-7003 will carry multiple scopes.
        result = await self._repository.scoped_search(action.querier, [action.scope])
        return ScopedSearchAppConfigFragmentActionResult(
            _scope=action.scope,
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def purge(
        self, action: PurgeAppConfigFragmentAction
    ) -> PurgeAppConfigFragmentActionResult:
        data = await self._repository.purge(action.purger_spec)
        return PurgeAppConfigFragmentActionResult(fragment=data)

    async def bulk_purge(
        self, action: BulkPurgeAppConfigFragmentAction
    ) -> BulkPurgeAppConfigFragmentActionResult:
        result = await self._repository.bulk_purge(action.purger_specs)
        return BulkPurgeAppConfigFragmentActionResult(
            succeeded=result.succeeded, failed=result.failed
        )
