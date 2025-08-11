import uuid
from collections.abc import Collection, Sequence
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from .models import (
    get_object_permissions_table,
    get_roles_table,
    get_scope_permissions_table,
)
from .types import RoleCreationInputGroup


def insert_if_data_exists(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        db_conn.execute(sa.insert(row_type), data)


def batch_insert_from_role_creation_input_group(
    db_conn: Connection, input_groups: Sequence[RoleCreationInputGroup]
) -> None:
    if not input_groups:
        return
    roles_table = get_roles_table()
    role_insert_stmt = sa.insert(roles_table).returning(roles_table.c.id)
    role_result = db_conn.execute(
        role_insert_stmt, [group.role.to_dict() for group in input_groups]
    )
    role_records = cast(list[uuid.UUID], role_result.all())

    scope_permission_values: list[dict[str, Any]] = []
    object_permission_values: list[dict[str, Any]] = []
    for group, role_id in zip(input_groups, role_records):
        for scope_permission in group.scope_permissions:
            scope_permission_input = scope_permission.to_input(role_id)
            scope_permission_values.append(scope_permission_input.to_dict())
        for object_permission in group.object_permissions:
            object_permission_input = object_permission.to_input(role_id)
            object_permission_values.append(object_permission_input.to_dict())

    insert_if_data_exists(db_conn, get_scope_permissions_table(), scope_permission_values)
    insert_if_data_exists(db_conn, get_object_permissions_table(), object_permission_values)
