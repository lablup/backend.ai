import uuid
from dataclasses import dataclass
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.vfolder import VFolderOwnershipType, VFolderPermissionRow, VFolderRow

ENTITY_TYPE = "vfolder"


@dataclass
class VFolderData:
    id: str
    user: Optional[str]
    group: Optional[str]
    ownership_type: VFolderOwnershipType

    def to_assoc_scope_entity_insert_dict(self) -> dict[str, Any]:
        return {
            "scope_type": "user" if self.ownership_type == VFolderOwnershipType.USER else "project",
            "scope_id": self.user
            if self.ownership_type == VFolderOwnershipType.USER
            else self.group,
            "entity_type": ENTITY_TYPE,
            "entity_id": self.id,
        }


@dataclass
class VFolderPermissionData:
    vfolder_id: str
    user_id: str
    permission: str

    def __hash__(self):
        return hash((self.vfolder_id, self.user_id, self.permission))

    def to_role_name(self) -> str:
        return f"vfolder_granted_{self.vfolder_id}"


def _migrate_vfolder_data_to_association_scopes_entities(conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        vfolder_query = (
            sa.select(VFolderRow).offset(offset).limit(page_size).order_by(VFolderRow.id)
        )
        result = conn.execute(vfolder_query)
        offset += page_size
        if result is None or result.rowcount == 0:
            break

        vfolder_list: list[VFolderData] = []
        for row in result:
            vfolder_list.append(
                VFolderData(
                    id=str(row["id"]),
                    user=str(row["user"]),
                    group=str(row["group"]),
                    ownership_type=row["ownership_type"],
                )
            )
        if not vfolder_list:
            break

        association_values = [
            vfolder.to_assoc_scope_entity_insert_dict() for vfolder in vfolder_list
        ]
        conn.execute(sa.insert(AssociationScopesEntitiesRow).values(association_values))


def _migrate_vfolder_permission_data_to_object_permissions(conn: Connection) -> None:
    offset = 0
    page_size = 1000
    inserted_permissions: set[VFolderPermissionData] = set()
    inserted_role_names: set[str] = set()
    inserted_vfolder_obj_perms: set[str] = set()
    while True:
        query_vfolder_permission = (
            sa.select(VFolderRow)
            .join(VFolderPermissionRow, VFolderRow.id == VFolderPermissionRow.vfolder)
            .offset(offset)
            .limit(page_size)
            .order_by(VFolderRow.id)
        )
        result = conn.execute(query_vfolder_permission)
        offset += page_size
        if result is None or result.rowcount == 0:
            break

        vfolder_perm_list: list[VFolderPermissionData] = []
        for row in result:
            perm_data = VFolderPermissionData(
                vfolder_id=str(row["id"]),
                user_id=str(row["user"]),
                permission=str(row["permission"]),
            )
            if perm_data in inserted_permissions:
                continue
            inserted_permissions.add(perm_data)
            vfolder_perm_list.append(perm_data)
        if not vfolder_perm_list:
            continue

        role_names = {perm.to_role_name() for perm in vfolder_perm_list}
        role_name_values = [{"name": name} for name in role_names]
        conn.execute(sa.insert(RoleRow).values(role_name_values))
        inserted_role_names.update(role_names)

        role_name_vfolder_id_map: dict[str, str] = {
            perm.to_role_name(): perm.vfolder_id for perm in vfolder_perm_list
        }
        query_role = sa.select(RoleRow).where(RoleRow.name.in_(role_name_vfolder_id_map.keys()))  # type: ignore[attr-defined]
        result = conn.execute(query_role)

        vfolder_id_role_id_map: dict[str, uuid.UUID] = {
            role_name_vfolder_id_map[row["name"]]: row["id"] for row in result
        }
        filtered_perm_list: list[VFolderPermissionData] = []
        for perm in vfolder_perm_list:
            if perm.vfolder_id in inserted_vfolder_obj_perms:
                continue
            inserted_vfolder_obj_perms.add(perm.vfolder_id)
            filtered_perm_list.append(perm)
        if not filtered_perm_list:
            continue
        object_permission_values = [
            {
                "role_id": vfolder_id_role_id_map[perm.vfolder_id],
                "entity_type": ENTITY_TYPE,
                "entity_id": perm.vfolder_id,
                "operation": "read",
            }
            for perm in filtered_perm_list
        ]
        conn.execute(sa.insert(ObjectPermissionRow).values(object_permission_values))


def migrate_vfolder_data(conn: Connection) -> None:
    _migrate_vfolder_data_to_association_scopes_entities(conn)
    _migrate_vfolder_permission_data_to_object_permissions(conn)
