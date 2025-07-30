"""migrate vfolder data to rbac table

Revision ID: 4a60160ba8e0
Revises: 643deb439458
Create Date: 2025-07-30 14:44:14.346887

"""

import uuid
from dataclasses import dataclass
from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "4a60160ba8e0"
down_revision = "643deb439458"
branch_labels = None
depends_on = None


@dataclass
class VFolderData:
    id: str
    user: Optional[str]
    group: Optional[str]
    ownership_type: str  # e.g., "user", "group"

    def to_insert_val(self) -> str:
        scope_type = "user" if self.ownership_type == "user" else "project"
        scope_id = self.user if self.ownership_type == "user" else self.group
        return f"('{scope_type}', '{scope_id}', 'vfolder', '{self.id}')"


@dataclass
class VFolderPermissionData:
    vfolder_id: str
    user_id: str
    permission: str

    def to_role_name(self) -> str:
        return f"vfolder_granted_{self.vfolder_id}"


def migrate_vfolder_data_to_association_scopes_entities(conn: Connection) -> None:
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


def migrate_vfolder_permission_data_to_object_permissions(conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        vfolder_permission_query = f"""
        SELECT v.id, p.user, p.permission FROM vfolders v
        JOIN vfolder_permissions p ON v.id = p.vfolder
        LIMIT {page_size} OFFSET {offset};
        """
        result = conn.execute(sa.text(vfolder_permission_query))
        if result is None or result.rowcount == 0:
            break

        vfolder_perm_list: list[VFolderPermissionData] = []
        for row in result:
            vfolder_perm_list.append(
                VFolderPermissionData(
                    vfolder_id=str(row["id"]),
                    user_id=str(row["user"]),
                    permission=str(row["permission"]),
                )
            )
        if not vfolder_perm_list:
            break

        role_name_values = ", ".join([f"('{perm.to_role_name()}')" for perm in vfolder_perm_list])
        insert_role_query = f"""
        INSERT INTO roles (name)
        SELECT name FROM (
            VALUES {role_name_values}
        ) AS new_roles (name)
        WHERE NOT EXISTS (
            SELECT 1 FROM roles r WHERE r.name = new_roles.name
        );
        """
        conn.execute(sa.text(insert_role_query))

        role_name_vfolder_id_map: dict[str, str] = {
            perm.to_role_name(): perm.vfolder_id for perm in vfolder_perm_list
        }
        role_names = ", ".join([f"'{role_name}'" for role_name in role_name_vfolder_id_map])
        role_id_query = f"""SELECT id, name FROM roles WHERE name IN ({role_names});"""
        result = conn.execute(sa.text(role_id_query))

        vfolder_id_role_id_map: dict[str, uuid.UUID] = {
            role_name_vfolder_id_map[row["name"]]: row["id"] for row in result
        }
        object_permission_values = ", ".join([
            f"('{vfolder_id_role_id_map[perm.vfolder_id]}', 'vfolder', '{perm.vfolder_id}', 'read')"
            for perm in vfolder_perm_list
        ])
        insert_object_permission_query = f"""
        INSERT INTO object_permissions (role_id, entity_type, entity_id, operation)
        VALUES {object_permission_values}
        """
        conn.execute(sa.text(insert_object_permission_query))

        offset += page_size


def upgrade() -> None:
    conn = op.get_bind()
    migrate_vfolder_data_to_association_scopes_entities(conn)
    migrate_vfolder_permission_data_to_object_permissions(conn)


def downgrade() -> None:
    pass
