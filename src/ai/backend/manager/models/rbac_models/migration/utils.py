from collections.abc import Collection

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from .models import (
    AssociationScopesEntitiesRow,
    ObjectPermissionRow,
    RoleRow,
    ScopePermissionRow,
    UserRoleRow,
)
from .types import PermissionCreateInputGroup


def _insert_if_data_exists(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        db_conn.execute(sa.insert(row_type), data)


def insert_from_create_input_group(
    db_conn: Connection, input_group: PermissionCreateInputGroup
) -> None:
    _insert_if_data_exists(db_conn, RoleRow, input_group.to_role_insert_data())
    _insert_if_data_exists(db_conn, UserRoleRow, input_group.to_user_role_insert_data())
    _insert_if_data_exists(
        db_conn, ScopePermissionRow, input_group.to_scope_permission_insert_data()
    )
    _insert_if_data_exists(
        db_conn, ObjectPermissionRow, input_group.to_object_permission_insert_data()
    )
    _insert_if_data_exists(
        db_conn,
        AssociationScopesEntitiesRow,
        input_group.to_association_scopes_entities_insert_data(),
    )
