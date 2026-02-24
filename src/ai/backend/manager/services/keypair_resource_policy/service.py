from __future__ import annotations

import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
    CreateKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
    DeleteKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_keypair_resource_policy import (
    GetKeyPairResourcePolicyAction,
    GetKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
    ModifyKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.search_keypair_resource_policies import (
    SearchKeyPairResourcePoliciesAction,
    SearchKeyPairResourcePoliciesActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KeypairResourcePolicyService:
    _keypair_resource_policy_repository: KeypairResourcePolicyRepository

    def __init__(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
    ) -> None:
        self._keypair_resource_policy_repository = keypair_resource_policy_repository

    async def get_keypair_resource_policy(
        self, action: GetKeyPairResourcePolicyAction
    ) -> GetKeyPairResourcePolicyActionResult:
        result = await self._keypair_resource_policy_repository.get_by_name(action.name)
        return GetKeyPairResourcePolicyActionResult(keypair_resource_policy=result)

    async def search_keypair_resource_policies(
        self, action: SearchKeyPairResourcePoliciesAction
    ) -> SearchKeyPairResourcePoliciesActionResult:
        result = await self._keypair_resource_policy_repository.search(action.querier)
        return SearchKeyPairResourcePoliciesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create_keypair_resource_policy(
        self, action: CreateKeyPairResourcePolicyAction
    ) -> CreateKeyPairResourcePolicyActionResult:
        result = await self._keypair_resource_policy_repository.create_keypair_resource_policy(
            action.creator
        )
        return CreateKeyPairResourcePolicyActionResult(keypair_resource_policy=result)

    async def modify_keypair_resource_policy(
        self, action: ModifyKeyPairResourcePolicyAction
    ) -> ModifyKeyPairResourcePolicyActionResult:
        result = await self._keypair_resource_policy_repository.update_keypair_resource_policy(
            action.updater
        )
        return ModifyKeyPairResourcePolicyActionResult(keypair_resource_policy=result)

    async def delete_keypair_resource_policy(
        self, action: DeleteKeyPairResourcePolicyAction
    ) -> DeleteKeyPairResourcePolicyActionResult:
        name = action.name
        result = await self._keypair_resource_policy_repository.remove_keypair_resource_policy(name)
        return DeleteKeyPairResourcePolicyActionResult(keypair_resource_policy=result)
