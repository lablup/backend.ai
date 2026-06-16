import logging

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItemError,
)
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentKey,
    AppConfigScopeType,
)
from ai.backend.manager.repositories.app_config_fragment.admin_repository import (
    AppConfigFragmentAdminRepository,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.my_bulk_create import (
    MyBulkCreateAppConfigFragmentsAction,
    MyBulkCreateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.my_bulk_update import (
    MyBulkUpdateAppConfigFragmentsAction,
    MyBulkUpdateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.search import (
    SearchAppConfigFragmentsAction,
    SearchAppConfigFragmentsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AppConfigFragmentService:
    """Non-admin operations available to any authenticated user.

    Self-service writes (`my_bulk_*`) target the caller's own `USER`
    scope; the actual row write goes through the shared admin repository
    while reads use the non-admin repository.
    """

    _repository: AppConfigFragmentRepository
    _admin_repository: AppConfigFragmentAdminRepository

    def __init__(
        self,
        repository: AppConfigFragmentRepository,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        self._repository = repository
        self._admin_repository = admin_repository

    async def get(self, action: GetAppConfigFragmentAction) -> GetAppConfigFragmentActionResult:
        fragment = await self._repository.get_by_key(action.key)
        return GetAppConfigFragmentActionResult(fragment=fragment)

    async def search(
        self, action: SearchAppConfigFragmentsAction
    ) -> SearchAppConfigFragmentsActionResult:
        result = await self._repository.scoped_search(action.querier, [action.scope])
        return SearchAppConfigFragmentsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def my_bulk_create(
        self, action: MyBulkCreateAppConfigFragmentsAction
    ) -> MyBulkCreateAppConfigFragmentsActionResult:
        """Self-service bulk create on the caller's `USER` row; each
        success recomputes the merged `AppConfig` view.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        user_id = me.user_id
        user_id_str = str(user_id)
        created = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, item in enumerate(action.items):
            key = AppConfigFragmentKey(
                scope_type=AppConfigScopeType.USER,
                scope_id=user_id_str,
                name=item.name,
            )
            try:
                await self._admin_repository.create(key, item.config)
                merged = await self._repository.app_config(user_id, item.name)
                created.append(merged)
            except Exception as e:
                log.warning("my_bulk_create item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=AppConfigScopeType.USER.value,
                        scope_id=user_id_str,
                        name=item.name,
                        message=str(e),
                    )
                )
        return MyBulkCreateAppConfigFragmentsActionResult(created=created, failed=failed)

    async def my_bulk_update(
        self, action: MyBulkUpdateAppConfigFragmentsAction
    ) -> MyBulkUpdateAppConfigFragmentsActionResult:
        """Self-service bulk update on the caller's `USER` row."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        user_id = me.user_id
        user_id_str = str(user_id)
        updated = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, item in enumerate(action.items):
            key = AppConfigFragmentKey(
                scope_type=AppConfigScopeType.USER,
                scope_id=user_id_str,
                name=item.name,
            )
            try:
                await self._admin_repository.update(key, item.config)
                merged = await self._repository.app_config(user_id, item.name)
                updated.append(merged)
            except Exception as e:
                log.warning("my_bulk_update item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=AppConfigScopeType.USER.value,
                        scope_id=user_id_str,
                        name=item.name,
                        message=str(e),
                    )
                )
        return MyBulkUpdateAppConfigFragmentsActionResult(updated=updated, failed=failed)
