from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.repositories.app_config_policy.admin_repository import (
    AppConfigPolicyAdminRepository,
)
from ai.backend.manager.repositories.app_config_policy.repository import (
    AppConfigPolicyRepository,
)
from ai.backend.manager.services.app_config_policy.actions.create import (
    CreateAppConfigPolicyAction,
    CreateAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.get import (
    GetAppConfigPolicyAction,
    GetAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.purge import (
    PurgeAppConfigPolicyAction,
    PurgeAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.search import (
    SearchAppConfigPoliciesAction,
    SearchAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.update import (
    UpdateAppConfigPolicyAction,
    UpdateAppConfigPolicyActionResult,
)


class AppConfigPolicyService:
    _repository: AppConfigPolicyRepository
    _admin_repository: AppConfigPolicyAdminRepository

    def __init__(
        self,
        repository: AppConfigPolicyRepository,
        admin_repository: AppConfigPolicyAdminRepository,
    ) -> None:
        self._repository = repository
        self._admin_repository = admin_repository

    async def get(self, action: GetAppConfigPolicyAction) -> GetAppConfigPolicyActionResult:
        policy = await self._repository.get(action.config_name)
        return GetAppConfigPolicyActionResult(policy=policy)

    async def search(
        self, action: SearchAppConfigPoliciesAction
    ) -> SearchAppConfigPoliciesActionResult:
        result = await self._admin_repository.search(action.querier)
        return SearchAppConfigPoliciesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create(
        self, action: CreateAppConfigPolicyAction
    ) -> CreateAppConfigPolicyActionResult:
        policy = await self._admin_repository.create(action.config_name, action.scope_sources)
        return CreateAppConfigPolicyActionResult(policy=policy)

    async def update(
        self, action: UpdateAppConfigPolicyAction
    ) -> UpdateAppConfigPolicyActionResult:
        policy = await self._admin_repository.update(action.config_name, action.scope_sources)
        if policy is None:
            raise ObjectNotFound(object_name=f"AppConfigPolicy({action.config_name})")
        return UpdateAppConfigPolicyActionResult(policy=policy)

    async def purge(self, action: PurgeAppConfigPolicyAction) -> PurgeAppConfigPolicyActionResult:
        purged = await self._admin_repository.purge(action.config_name)
        return PurgeAppConfigPolicyActionResult(
            config_name=action.config_name,
            purged=purged,
        )
