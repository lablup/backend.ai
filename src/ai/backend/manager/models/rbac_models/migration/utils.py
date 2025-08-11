from collections.abc import Collection, Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from .models import (
    get_association_scopes_entities_table,
    get_user_roles_table,
)
from .types import UserRoleMappingInputGroup


def insert_if_data_exists(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        db_conn.execute(sa.insert(row_type), data)


def insert_from_user_role_mapping_input_group(
    db_conn: Connection, input_groups: Sequence[UserRoleMappingInputGroup]
) -> None:
    user_roles: list[dict[str, Any]] = []
    scope_entities: list[dict[str, Any]] = []
    for group in input_groups:
        user_roles.append(group.user_role_input.to_dict())
        scope_entities.append(group.association_scopes_entities_input.to_dict())
    insert_if_data_exists(db_conn, get_user_roles_table(), user_roles)
    insert_if_data_exists(db_conn, get_association_scopes_entities_table(), scope_entities)
