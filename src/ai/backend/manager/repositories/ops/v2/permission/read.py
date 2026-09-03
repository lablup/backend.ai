"""Permission reads: what a role holds per (scope, entity_type) key, field scopes
included, composed from the per-bit rows and their path rows."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.permission.id import FieldPath
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_field import PermissionFieldRow
from ai.backend.manager.models.specs.permission import PermissionEntry, PermissionKey
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps


class PermissionReadOps(V2ReadOps):
    """The general v2 read ops plus the role permission read."""

    async def permissions(
        self, role_id: RoleID, keys: Sequence[PermissionKey]
    ) -> dict[PermissionKey, PermissionEntry]:
        """The named keys' entries; a key holding nothing is absent."""
        if not keys:
            return {}
        by_columns = {
            (str(k.scope.entity_type()), str(k.scope), str(k.entity_type)): k for k in keys
        }
        rows = (
            await self._sess.execute(
                sa.select(
                    PermissionRow.scope_type,
                    PermissionRow.scope_id,
                    PermissionRow.entity_type,
                    PermissionRow.permission,
                    PermissionRow.all_fields,
                    PermissionFieldRow.path,
                )
                .select_from(PermissionRow)
                .outerjoin(PermissionFieldRow, PermissionFieldRow.permission_id == PermissionRow.id)
                .where(
                    PermissionRow.role_id == role_id,
                    self._key_filter(keys),
                )
            )
        ).all()
        whole: dict[PermissionKey, Permission] = {}
        fields: dict[PermissionKey, dict[FieldPath, Permission]] = {}
        for row in rows:
            key = by_columns[(str(row.scope_type), row.scope_id, str(row.entity_type))]
            whole.setdefault(key, Permission.NONE)
            if row.all_fields:
                whole[key] |= row.permission
            elif row.path is not None:
                scoped = fields.setdefault(key, {})
                scoped[row.path] = scoped.get(row.path, Permission.NONE) | row.permission
        return {
            key: PermissionEntry(
                scope=key.scope,
                entity_type=key.entity_type,
                permission=whole[key],
                fields=fields.get(key, {}),
            )
            for key in whole
        }

    def _key_filter(self, keys: Sequence[PermissionKey]) -> sa.ColumnElement[bool]:
        return sa.tuple_(
            PermissionRow.scope_type, PermissionRow.scope_id, PermissionRow.entity_type
        ).in_([self._key_columns(k.scope, k.entity_type) for k in keys])

    def _key_columns(
        self, scope: EntityIdentifier, entity_type: EntityType
    ) -> tuple[EntityType, str, EntityType]:
        return (scope.entity_type(), str(scope), entity_type)
