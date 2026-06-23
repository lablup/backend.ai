from __future__ import annotations

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigScopeType as AllowListScopeType,
)
from ai.backend.manager.data.app_config_fragment.types import AppConfigScopeType
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentForbidden,
    AppConfigFragmentWriteNotAllowed,
)
from ai.backend.manager.models.app_config_allow_list.conditions import (
    AppConfigAllowListConditions,
)
from ai.backend.manager.repositories.app_config_allow_list.repository import (
    AppConfigAllowListRepository,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
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
from ai.backend.manager.services.app_config_fragment.actions.search import (
    SearchAppConfigFragmentAction,
    SearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
    UpdateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.update_my import (
    UpdateMyAppConfigFragmentAction,
    UpdateMyAppConfigFragmentActionResult,
)
from ai.backend.manager.types import OptionalState

__all__ = ("AppConfigFragmentService",)


class AppConfigFragmentService:
    """Admin and self-service write paths for app config fragments.

    Every write passes the allow-list write-gate: a fragment may only be written when an
    ``app_config_allow_list`` row exists for its ``(config_name, scope_type)``. Because an
    allow-list row itself requires a registered ``config_name`` (FK to
    ``app_config_definitions``), this single check also enforces registration.
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

    async def _assert_write_allowed(self, config_name: str, scope_type: AppConfigScopeType) -> None:
        result = await self._allow_list_repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=1, offset=0),
                conditions=[
                    AppConfigAllowListConditions.by_config_name_equals(
                        StringMatchSpec(config_name, case_insensitive=False, negated=False)
                    ),
                    AppConfigAllowListConditions.by_scope_type_equals(
                        AllowListScopeType(scope_type.value)
                    ),
                ],
            )
        )
        if result.total_count == 0:
            raise AppConfigFragmentWriteNotAllowed(
                f"Writing app config {config_name!r} at scope {scope_type.value!r} is not allowed."
            )

    async def create(
        self, action: CreateAppConfigFragmentAction
    ) -> CreateAppConfigFragmentActionResult:
        await self._assert_write_allowed(
            action.creator_spec.config_name, action.creator_spec.scope_type
        )
        data = await self._repository.create(action.creator_spec)
        return CreateAppConfigFragmentActionResult(fragment=data)

    async def get(self, action: GetAppConfigFragmentAction) -> GetAppConfigFragmentActionResult:
        data = await self._repository.get_by_id(action.fragment_id)
        return GetAppConfigFragmentActionResult(fragment=data)

    async def search(
        self, action: SearchAppConfigFragmentAction
    ) -> SearchAppConfigFragmentActionResult:
        result = await self._repository.search(action.querier)
        return SearchAppConfigFragmentActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def update(
        self, action: UpdateAppConfigFragmentAction
    ) -> UpdateAppConfigFragmentActionResult:
        existing = await self._repository.get_by_id(action.fragment_id)
        await self._assert_write_allowed(existing.config_name, existing.scope_type)
        data = await self._repository.update(action.fragment_id, action.updater_spec)
        return UpdateAppConfigFragmentActionResult(fragment=data)

    async def update_my(
        self, action: UpdateMyAppConfigFragmentAction
    ) -> UpdateMyAppConfigFragmentActionResult:
        existing = await self._repository.get_by_id(action.fragment_id)
        if existing.scope_type is not AppConfigScopeType.USER or existing.scope_id != str(
            action.user_id
        ):
            raise AppConfigFragmentForbidden(
                f"Fragment {action.fragment_id} is not your own user-scope fragment."
            )
        await self._assert_write_allowed(existing.config_name, existing.scope_type)
        data = await self._repository.update(
            action.fragment_id,
            AppConfigFragmentUpdaterSpec(config=OptionalState.update(action.config)),
        )
        return UpdateMyAppConfigFragmentActionResult(fragment=data)

    async def purge(
        self, action: PurgeAppConfigFragmentAction
    ) -> PurgeAppConfigFragmentActionResult:
        data = await self._repository.purge(action.fragment_id)
        return PurgeAppConfigFragmentActionResult(fragment=data)
