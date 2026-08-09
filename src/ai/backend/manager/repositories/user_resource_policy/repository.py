from __future__ import annotations

from uuid import UUID

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.user_resource_policy.db_source.db_source import (
    UserResourcePolicyDBSource,
)


class UserResourcePolicyRepository:
    """The two reads the generic ops cannot answer.

    ``get_by_user_id`` joins through ``users``, which the single-table lookup spec
    rules out; ``get_by_name`` stays because the auth service reads a policy
    outside the action layer.
    """

    _db_source: UserResourcePolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = UserResourcePolicyDBSource(db)

    async def get_by_user_id(self, user_id: UUID) -> UserResourcePolicyData:
        return await self._db_source.get_by_user_id(user_id)

    async def get_by_name(self, name: str) -> UserResourcePolicyData:
        return await self._db_source.get_by_name(name)
