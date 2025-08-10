from collections.abc import Collection

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from .models import (
    get_association_scopes_entities_table,
    get_object_permissions_table,
    get_roles_table,
    get_scope_permissions_table,
    get_user_roles_table,
)
from .types import PermissionCreateInputGroup


def _insert_if_data_exists(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        db_conn.execute(sa.insert(row_type), data)


def insert_from_create_input_group(
    db_conn: Connection, input_group: PermissionCreateInputGroup
) -> None:
    _insert_if_data_exists(db_conn, get_roles_table(), input_group.to_role_insert_data())
    _insert_if_data_exists(db_conn, get_user_roles_table(), input_group.to_user_role_insert_data())
    _insert_if_data_exists(
        db_conn, get_scope_permissions_table(), input_group.to_scope_permission_insert_data()
    )
    _insert_if_data_exists(
        db_conn, get_object_permissions_table(), input_group.to_object_permission_insert_data()
    )
    _insert_if_data_exists(
        db_conn,
        get_association_scopes_entities_table(),
        input_group.to_association_scopes_entities_insert_data(),
    )
