import uuid
from collections.abc import Collection

import sqlalchemy as sa
from sqlalchemy.engine import Connection
from sqlalchemy.engine.row import Row

from .models import (
    get_permission_groups_table,
    get_roles_table,
)


def insert_if_data_exists(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        db_conn.execute(sa.insert(row_type), data)


def query_role_rows_by_name(db_conn: Connection, role_names: Collection[str]) -> list[Row]:
    """
    Query role rows by their names.
    """
    roles_table = get_roles_table()
    role_query = sa.select(roles_table).where(roles_table.c.name.in_(role_names))
    return db_conn.execute(role_query).all()


def query_permission_groups_by_scope_ids(
    db_conn: Connection, scope_ids: Collection[str]
) -> list[uuid.UUID]:
    """
    Query permission groups by scope IDs.
    """
    permission_groups_table = get_permission_groups_table()
    query = sa.select(permission_groups_table.c.id).where(
        permission_groups_table.c.scope_id.in_(scope_ids)
    )
    return db_conn.scalars(query).all()
