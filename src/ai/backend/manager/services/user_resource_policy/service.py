from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.user_resource_policy.actions.get_my_user_resource_policy import (
    GetMyUserResourcePolicyAction,
    GetMyUserResourcePolicyActionResult,
)


class UserResourcePolicyService:
    """The one operation that is not a pass-through.

    Resolving the caller's own policy joins through ``users``, which a
    ``DataLookup`` cannot express — a lookup spec stays on one table by design —
    so this read keeps a repository method and a service around it. Every other
    operation wires straight to the generic ops services.
    """

    _user_resource_policy_repository: UserResourcePolicyRepository

    def __init__(
        self,
        user_resource_policy_repository: UserResourcePolicyRepository,
    ) -> None:
        self._user_resource_policy_repository = user_resource_policy_repository

    async def get_my_user_resource_policy(
        self, action: GetMyUserResourcePolicyAction
    ) -> GetMyUserResourcePolicyActionResult:
        data = await self._user_resource_policy_repository.get_by_user_id(action.user_id)
        return GetMyUserResourcePolicyActionResult(data=data)
