import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.retention_policy.repository import RetentionPolicyRepository
from ai.backend.manager.services.retention_policy.actions.create import (
    CreateRetentionPolicyAction,
    CreateRetentionPolicyActionResult,
)
from ai.backend.manager.services.retention_policy.actions.delete import (
    DeleteRetentionPolicyAction,
    DeleteRetentionPolicyActionResult,
)
from ai.backend.manager.services.retention_policy.actions.purge import (
    PurgeRetentionPolicyAction,
    PurgeRetentionPolicyActionResult,
)
from ai.backend.manager.services.retention_policy.actions.search import (
    SearchRetentionPoliciesAction,
    SearchRetentionPoliciesActionResult,
)
from ai.backend.manager.services.retention_policy.actions.update import (
    UpdateRetentionPolicyAction,
    UpdateRetentionPolicyActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RetentionPolicyService:
    _repository: RetentionPolicyRepository

    def __init__(self, repository: RetentionPolicyRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateRetentionPolicyAction
    ) -> CreateRetentionPolicyActionResult:
        data = await self._repository.create(action.creator)
        return CreateRetentionPolicyActionResult(policy=data)

    async def update(
        self, action: UpdateRetentionPolicyAction
    ) -> UpdateRetentionPolicyActionResult:
        action.updater.pk_value = action.id
        data = await self._repository.update(action.updater)
        return UpdateRetentionPolicyActionResult(policy=data)

    async def delete(
        self, action: DeleteRetentionPolicyAction
    ) -> DeleteRetentionPolicyActionResult:
        data = await self._repository.delete(action.id)
        return DeleteRetentionPolicyActionResult(policy=data)

    async def purge(self, action: PurgeRetentionPolicyAction) -> PurgeRetentionPolicyActionResult:
        data = await self._repository.purge(action.purger)
        return PurgeRetentionPolicyActionResult(policy=data)

    async def search(
        self, action: SearchRetentionPoliciesAction
    ) -> SearchRetentionPoliciesActionResult:
        result = await self._repository.search(action.querier)
        return SearchRetentionPoliciesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
