import uuid
from dataclasses import dataclass
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.engine import Connection


@dataclass
class VFolderData:
    id: str
    user: Optional[str]
    group: Optional[str]
    ownership_type: str  # e.g., "user", "group"

    def to_insert_val(self) -> str:
        scope_type = "user" if self.ownership_type == "user" else "project"
        scope_id = self.user if self.ownership_type == "user" else self.group
        return f"('{scope_type}', '{scope_id}'::uuid, 'vfolder', '{self.id}'::uuid)"


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
        vfolder_query = f"""
        SELECT v.id, v.user, v.group, v.ownership_type FROM vfolders v
        LIMIT {page_size} OFFSET {offset};
        """
        result = conn.execute(sa.text(vfolder_query))
        if result is None or result.rowcount == 0:
            break

        vfolder_list: list[VFolderData] = []
        for row in result:
            vfolder_list.append(
                VFolderData(
                    id=str(row["id"]),
                    user=str(row["user"]),
                    group=str(row["group"]),
                    ownership_type=str(row["ownership_type"]),
                )
            )
        if not vfolder_list:
            break

        values = ", ".join([vfolder.to_insert_val() for vfolder in vfolder_list])
        insert_entity_query = f"""
        INSERT INTO association_scopes_entities (scope_type, scope_id, entity_type, entity_id)
        VALUES {values}
        """
        conn.execute(sa.text(insert_entity_query))

        offset += page_size


def _migrate_vfolder_permission_data_to_object_permissions(conn: Connection) -> None:
    offset = 0
    page_size = 1000
    inserted_permissions: set[VFolderPermissionData] = set()
    inserted_role_names: set[str] = set()
    inserted_vfolder_obj_perms: set[str] = set()
    while True:
        vfolder_permission_query = f"""
        SELECT v.id, p.user, p.permission FROM vfolders v
        JOIN vfolder_permissions p ON v.id = p.vfolder
        ORDER BY v.id
        LIMIT {page_size} OFFSET {offset};
        """
        offset += page_size
        result = conn.execute(sa.text(vfolder_permission_query))
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
        role_name_values = ", ".join([f"('{name}')" for name in role_names])
        insert_role_query = f"""
        INSERT INTO roles (name)
        VALUES {role_name_values};
        """
        conn.execute(sa.text(insert_role_query))
        inserted_role_names.update(role_names)

        role_name_vfolder_id_map: dict[str, str] = {
            perm.to_role_name(): perm.vfolder_id for perm in vfolder_perm_list
        }
        role_names_str = ", ".join([f"'{role_name}'" for role_name in role_name_vfolder_id_map])
        role_id_query = f"""SELECT id, name FROM roles WHERE name IN ({role_names_str});"""
        result = conn.execute(sa.text(role_id_query))

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
        object_permission_values = ", ".join([
            f"('{vfolder_id_role_id_map[perm.vfolder_id]}'::uuid, 'vfolder', '{perm.vfolder_id}'::uuid, 'read')"
            for perm in filtered_perm_list
        ])
        insert_object_permission_query = f"""
        INSERT INTO object_permissions (role_id, entity_type, entity_id, operation)
        VALUES {object_permission_values};
        """
        conn.execute(sa.text(insert_object_permission_query))


def migrate_vfolder_data(conn: Connection) -> None:
    _migrate_vfolder_data_to_association_scopes_entities(conn)
    _migrate_vfolder_permission_data_to_object_permissions(conn)
