from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    Any,
    override,
)

import sqlalchemy as sa

from ai.backend.manager.data.permission.permission_defs import StorageHostPermission

from .rbac import (
    AbstractPermissionContext,
)

StorageHostToPermissionMap = Mapping[str, frozenset[StorageHostPermission]]


@dataclass
class PermissionContext(AbstractPermissionContext[StorageHostPermission, str, str]):
    @property
    def host_to_permissions_map(self) -> StorageHostToPermissionMap:
        return self.object_id_to_additional_permission_map

    @override
    async def build_query(self) -> sa.sql.Select[Any] | None:
        return None

    @override
    async def calculate_final_permission(self, rbac_obj: str) -> frozenset[StorageHostPermission]:
        host_name = rbac_obj
        return self.object_id_to_additional_permission_map.get(host_name, frozenset())
