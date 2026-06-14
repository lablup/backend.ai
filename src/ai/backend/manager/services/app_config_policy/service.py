from ai.backend.manager.repositories.app_config_policy.repository import (
    AppConfigPolicyRepository,
)
from ai.backend.manager.services.app_config_policy.actions.get import (
    GetAppConfigPolicyAction,
    GetAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.scoped_search import (
    ScopedSearchAppConfigPoliciesAction,
    ScopedSearchAppConfigPoliciesActionResult,
)


class AppConfigPolicyService:
    """Non-admin operations available to any authenticated user."""

    _repository: AppConfigPolicyRepository

    def __init__(self, repository: AppConfigPolicyRepository) -> None:
        self._repository = repository

    async def get(self, action: GetAppConfigPolicyAction) -> GetAppConfigPolicyActionResult:
        policy = await self._repository.get_by_id(action.id)
        return GetAppConfigPolicyActionResult(policy=policy)

    async def scoped_search(
        self, action: ScopedSearchAppConfigPoliciesAction
    ) -> ScopedSearchAppConfigPoliciesActionResult:
        targets = list(action.targets())
        scopes = [t.to_search_scope() for t in targets]
        result = await self._repository.scoped_search(action.querier, scopes)
        return ScopedSearchAppConfigPoliciesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            queried_refs=[t.to_rbac_element_ref() for t in targets],
        )
