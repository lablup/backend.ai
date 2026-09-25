"""The bits a user effectively holds, read through the permission ops."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_entity import (
    GovernCheckKey,
    OwnCheckKey,
    PermissionCheckResult,
)
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider

__all__ = ("RbacPermissionCheckRepository",)


class RbacPermissionCheckRepository:
    """What the action gates ask before a run: own for an entity, govern for a scope.

    With enforcement off every key holds every bit.
    """

    _ops: PermissionOpsProvider
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        ops_provider: PermissionOpsProvider,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._ops = ops_provider
        self._config_provider = config_provider

    async def owned_permissions(
        self, keys: Collection[OwnCheckKey]
    ) -> Mapping[OwnCheckKey, Permission]:
        if not self._enforced():
            return dict.fromkeys(keys, Permission.full())
        async with self._ops.read_ops() as r:
            return await r.owned_permissions(keys)

    async def governed_permissions(
        self, keys: Collection[GovernCheckKey]
    ) -> Mapping[GovernCheckKey, Permission]:
        if not self._enforced():
            return dict.fromkeys(keys, Permission.full())
        async with self._ops.read_ops() as r:
            return await r.governed_permissions(keys)

    async def checked_permissions(
        self,
        govern_keys: Sequence[GovernCheckKey],
        own_keys: Sequence[OwnCheckKey],
    ) -> PermissionCheckResult:
        """Both checks of one run, answered in a single read session."""
        if not self._enforced():
            return PermissionCheckResult(
                governed=dict.fromkeys(govern_keys, Permission.full()),
                owned=dict.fromkeys(own_keys, Permission.full()),
            )
        async with self._ops.read_ops() as r:
            return PermissionCheckResult(
                governed=await r.governed_permissions(govern_keys),
                owned=await r.owned_permissions(own_keys),
            )

    async def held_permissions(
        self, user_id: UserID, entity_ids: Sequence[EntityIdentifier]
    ) -> Mapping[EntityIdentifier, Permission]:
        """The bits one user holds on each entity, keyed by the entity."""
        keys = [OwnCheckKey(user_id=user_id, entity=entity_id) for entity_id in entity_ids]
        owned = await self.owned_permissions(keys)
        return {key.entity: owned.get(key, Permission.NONE) for key in keys}

    def _enforced(self) -> bool:
        return self._config_provider.config.manager.rbac.enforcement_enabled
