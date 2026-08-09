from __future__ import annotations

from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_my_keypair_resource_policy import (
    GetMyKeypairResourcePolicyAction,
    GetMyKeypairResourcePolicyActionResult,
)


class KeypairResourcePolicyService:
    """The one operation that is not a pass-through.

    Resolving the caller's own policy joins through ``keypairs`` and filters on the
    keypair being active, which a ``DataLookup`` cannot express — a lookup spec stays
    on one table by design. Every other operation wires straight to the generic ops
    services.
    """

    _keypair_resource_policy_repository: KeypairResourcePolicyRepository

    def __init__(
        self,
        keypair_resource_policy_repository: KeypairResourcePolicyRepository,
    ) -> None:
        self._keypair_resource_policy_repository = keypair_resource_policy_repository

    async def get_my_keypair_resource_policy(
        self, action: GetMyKeypairResourcePolicyAction
    ) -> GetMyKeypairResourcePolicyActionResult:
        data = await self._keypair_resource_policy_repository.get_by_user_id(action.user_id)
        return GetMyKeypairResourcePolicyActionResult(data=data)
