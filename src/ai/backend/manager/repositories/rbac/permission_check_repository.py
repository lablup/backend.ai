"""The bits a user effectively holds, read through the permission ops."""

from __future__ import annotations

from collections.abc import Collection, Mapping

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey, OwnCheckKey
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider

__all__ = ("RbacPermissionCheckRepository",)


class RbacPermissionCheckRepository:
    """What the action gates ask before a run: own for an entity, govern for a scope."""

    _ops: PermissionOpsProvider

    def __init__(self, ops_provider: PermissionOpsProvider) -> None:
        self._ops = ops_provider

    async def owned_permissions(
        self, keys: Collection[OwnCheckKey]
    ) -> Mapping[OwnCheckKey, Permission]:
        async with self._ops.read_ops() as r:
            return await r.owned_permissions(keys)

    async def governed_permissions(
        self, keys: Collection[GovernCheckKey]
    ) -> Mapping[GovernCheckKey, Permission]:
        async with self._ops.read_ops() as r:
            return await r.governed_permissions(keys)
