from __future__ import annotations

from typing import cast

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.errors.app_config import AppConfigFragmentWriteNotAllowed
from ai.backend.manager.models.app_config_allow_list.conditions import (
    AppConfigAllowListConditions,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.app_config_allow_list.repository import (
    AppConfigAllowListRepository,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.base import ExistsQuerier
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
    """Write paths for app config fragments (not admin-only).

    ``create``, ``update``, and ``purge`` all pass the allow-list write-gate: a fragment may
    only be written or removed when an ``app_config_allow_list`` row exists for its
    ``(config_name, scope_type)``. Because an allow-list row itself requires a registered
    ``config_name`` (FK to ``app_config_definitions``), this single check also enforces
    registration. An allow-listed user may therefore manage their own ``user``-scope
    fragment without admin privileges.
    """

    _repository: AppConfigFragmentRepository
    _allow_list_repository: AppConfigAllowListRepository

    def __init__(
        self,
        repository: AppConfigFragmentRepository,
        allow_list_repository: AppConfigAllowListRepository,
    ) -> None:
        self._repository = repository
        self._allow_list_repository = allow_list_repository

    async def _ensure_write_allowed(self, config_name: str, scope_type: AppConfigScopeType) -> None:
        allowed = await self._allow_list_repository.exists(
            ExistsQuerier(
                row_class=AppConfigAllowListRow,
                conditions=[
                    AppConfigAllowListConditions.by_config_name_equals(
                        StringMatchSpec(config_name, case_insensitive=False, negated=False)
                    ),
                    AppConfigAllowListConditions.by_scope_type_equals(scope_type),
                ],
            )
        )
        if not allowed:
            raise AppConfigFragmentWriteNotAllowed(
                f"Writing app config {config_name!r} at scope {scope_type.value!r} is not allowed."
            )

    async def create(
        self, action: CreateAppConfigFragmentAction
    ) -> CreateAppConfigFragmentActionResult:
        await self._ensure_write_allowed(
            action.creator_spec.config_name, action.creator_spec.scope_type
        )
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
        existing = await self._repository.get_by_id(
            cast(AppConfigFragmentID, action.updater.pk_value)
        )
        await self._ensure_write_allowed(existing.config_name, existing.scope_type)
        data = await self._repository.update(action.updater)
        return UpdateAppConfigFragmentActionResult(fragment=data)

    async def purge(
        self, action: PurgeAppConfigFragmentAction
    ) -> PurgeAppConfigFragmentActionResult:
        existing = await self._repository.get_by_id(
            cast(AppConfigFragmentID, action.purger.pk_value)
        )
        await self._ensure_write_allowed(existing.config_name, existing.scope_type)
        data = await self._repository.purge(action.purger)
        return PurgeAppConfigFragmentActionResult(fragment=data)
