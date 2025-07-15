import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
    CreateUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
    DeleteUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
    ModifyUserResourcePolicyActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserResourcePolicyService:
    _user_resource_policy_repository: UserResourcePolicyRepository

    def __init__(
        self,
        user_resource_policy_repository: UserResourcePolicyRepository,
    ) -> None:
        self._user_resource_policy_repository = user_resource_policy_repository

    async def create_user_resource_policy(
        self, action: CreateUserResourcePolicyAction
    ) -> CreateUserResourcePolicyActionResult:
        creator = action.creator
        to_create = creator.fields_to_store()
        result = await self._user_resource_policy_repository.create(to_create)
        return CreateUserResourcePolicyActionResult(user_resource_policy=result)

    async def modify_user_resource_policy(
        self, action: ModifyUserResourcePolicyAction
    ) -> ModifyUserResourcePolicyActionResult:
        name = action.name
        modifier = action.modifier
        to_update = modifier.fields_to_update()
        result = await self._user_resource_policy_repository.update(name, to_update)
        return ModifyUserResourcePolicyActionResult(user_resource_policy=result)

    async def delete_user_resource_policy(
        self, action: DeleteUserResourcePolicyAction
    ) -> DeleteUserResourcePolicyActionResult:
        name = action.name
        result = await self._user_resource_policy_repository.delete(name)
        return DeleteUserResourcePolicyActionResult(user_resource_policy=result)
