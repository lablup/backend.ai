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
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
    ModifyKeyPairResourcePolicyActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KeypairResourcePolicyService:
    _keypair_resource_policy_repository: KeypairResourcePolicyRepository

    def __init__(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
    ) -> None:
        self._keypair_resource_policy_repository = keypair_resource_policy_repository

    async def create_keypair_resource_policy(
        self, action: CreateKeyPairResourcePolicyAction
    ) -> CreateKeyPairResourcePolicyActionResult:
        to_store = action.creator.fields_to_store()
        result = await self._keypair_resource_policy_repository.create(to_store)
        return CreateKeyPairResourcePolicyActionResult(keypair_resource_policy=result)

    async def modify_keypair_resource_policy(
        self, action: ModifyKeyPairResourcePolicyAction
    ) -> ModifyKeyPairResourcePolicyActionResult:
        name = action.name
        props = action.modifier
        to_update = props.fields_to_update()
        result = await self._keypair_resource_policy_repository.update(name, to_update)
        return ModifyKeyPairResourcePolicyActionResult(keypair_resource_policy=result)

    async def delete_keypair_resource_policy(
        self, action: DeleteKeyPairResourcePolicyAction
    ) -> DeleteKeyPairResourcePolicyActionResult:
        name = action.name
        result = await self._keypair_resource_policy_repository.delete(name)
        return DeleteKeyPairResourcePolicyActionResult(keypair_resource_policy=result)
