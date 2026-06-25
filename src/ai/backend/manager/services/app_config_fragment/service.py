from __future__ import annotations

from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
    AdminSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
    CreateAppConfigFragmentActionResult,
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
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
    UpdateAppConfigFragmentActionResult,
)

__all__ = ("AppConfigFragmentService",)


class AppConfigFragmentService:
    """Write/read paths for app config fragments (not admin-only).

    ``create`` / ``update`` / ``purge`` are gated by the allow-list write-gate in the
    repository: the gate check and the write run in a single transaction, so a fragment is
    only written or removed when an ``app_config_allow_list`` row exists for its
    ``(config_name, scope_type)``. Because an allow-list row requires a registered
    ``config_name`` (FK), this also enforces registration. An allow-listed user may
    therefore manage their own ``user``-scope fragment without admin privileges.
    """

    _repository: AppConfigFragmentRepository

    def __init__(self, repository: AppConfigFragmentRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateAppConfigFragmentAction
    ) -> CreateAppConfigFragmentActionResult:
        data = await self._repository.create(action.creator_spec)
        return CreateAppConfigFragmentActionResult(fragment=data)

    async def get(self, action: GetAppConfigFragmentAction) -> GetAppConfigFragmentActionResult:
        data = await self._repository.get_by_id(action.fragment_id)
        return GetAppConfigFragmentActionResult(fragment=data)

    async def admin_search(
        self, action: AdminSearchAppConfigFragmentAction
    ) -> AdminSearchAppConfigFragmentActionResult:
        result = await self._repository.admin_search(action.querier)
        return AdminSearchAppConfigFragmentActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def scoped_search(
        self, action: ScopedSearchAppConfigFragmentAction
    ) -> ScopedSearchAppConfigFragmentActionResult:
        targets = list(action.targets())
        scopes = [t.to_search_scope() for t in targets]
        result = await self._repository.scoped_search(action.querier, scopes)
        return ScopedSearchAppConfigFragmentActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            queried_refs=[t.to_rbac_element_ref() for t in targets],
        )

    async def update(
        self, action: UpdateAppConfigFragmentAction
    ) -> UpdateAppConfigFragmentActionResult:
        data = await self._repository.update(action.updater)
        return UpdateAppConfigFragmentActionResult(fragment=data)

    async def purge(
        self, action: PurgeAppConfigFragmentAction
    ) -> PurgeAppConfigFragmentActionResult:
        data = await self._repository.purge(action.purger)
        return PurgeAppConfigFragmentActionResult(fragment=data)
