from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.rbac_models.permission.lookups import RolePermissionOwnerLookup


@dataclass(frozen=True)
class PermissionIDLookupKey(LookupKey):
    """A permission entry's id, resolved into the role that holds it."""

    permission_id: PermissionID

    @override
    def kind(self) -> str:
        return "permission_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.permission_id)}


@dataclass
class LookupRolePermissionOwnerAction(LookupFieldOwnerOpsAction[PermissionID, RoleID]):
    """The role a permission entry belongs to."""

    permission_id: PermissionID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_role_permission_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return PermissionIDLookupKey(self.permission_id)

    @override
    def field_id(self) -> PermissionID:
        return self.permission_id

    @override
    def to_owner_lookup(self) -> RolePermissionOwnerLookup:
        return RolePermissionOwnerLookup()


@dataclass
class LookupBulkRolePermissionOwnerAction(LookupBulkFieldOwnerOpsAction[PermissionID, RoleID]):
    """The roles several permission entries belong to."""

    permission_ids: Sequence[PermissionID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_role_permission_owner"

    @override
    def to_lookup_key(self, field_id: PermissionID) -> LookupKey:
        return PermissionIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[PermissionID]:
        return tuple(self.permission_ids)

    @override
    def to_owner_lookup(self) -> RolePermissionOwnerLookup:
        return RolePermissionOwnerLookup()
