import uuid
from collections.abc import Collection
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection
from sqlalchemy.engine.row import Row

from .enums import EntityType, OperationType, ScopeType
from .models import (
    get_permission_groups_table,
    get_permissions_table,
    get_roles_table,
)
from .types import (
    GLOBAL_SCOPE_ID,
    PermissionCreateInput,
    PermissionGroupCreateInput,
    RoleCreateInput,
)


def insert_if_data_exists(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        db_conn.execute(sa.insert(row_type), data)


def insert_skip_on_conflict(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        stmt = pg_insert(row_type, data).on_conflict_do_nothing()
        db_conn.execute(stmt)


def insert_and_returning_id(
    db_conn: Connection,
    row_type,
    data: Any,
) -> uuid.UUID:
    stmt = sa.insert(row_type).values(data).returning(row_type.c.id)
    result = db_conn.execute(stmt)
    return result.scalar_one()


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


class PermissionUpdateUtil:
    @staticmethod
    def get_or_create_role(db_conn: Connection, role_input: RoleCreateInput) -> uuid.UUID:
        roles_table = get_roles_table()
        result = db_conn.execute(
            sa.select(roles_table).where(
                sa.and_(
                    roles_table.c.name == role_input.name,
                    roles_table.c.source == role_input.source,
                )
            )
        )
        role_row = result.fetchone()
        if role_row is not None:
            return role_row.id
        else:
            role_id = insert_and_returning_id(
                db_conn,
                roles_table,
                role_input.to_dict(),
            )
            return role_id

    @staticmethod
    def get_or_create_global_permission_group(
        db_conn: Connection, role_id: uuid.UUID
    ) -> tuple[uuid.UUID, bool]:
        """
        Get or create a global permission group for the given role ID.
        Returns a tuple of (permission_group_id, already_exists).
        """
        permission_groups_table = get_permission_groups_table()
        result = db_conn.execute(
            sa.select(permission_groups_table.c.id).where(
                sa.and_(
                    permission_groups_table.c.role_id == role_id,
                    permission_groups_table.c.scope_id == GLOBAL_SCOPE_ID,
                )
            )
        )
        permission_group_row = result.fetchone()
        if permission_group_row is not None:
            return permission_group_row.id, True
        else:
            input = (
                PermissionGroupCreateInput(
                    role_id=role_id,
                    scope_type=ScopeType.GLOBAL,
                    scope_id=GLOBAL_SCOPE_ID,
                )
            ).to_dict()
            permission_group_id = insert_and_returning_id(
                db_conn,
                permission_groups_table,
                input,
            )
            return permission_group_id, False

    @staticmethod
    def create_permissions(
        db_conn: Connection,
        permission_group_id: uuid.UUID,
        entity_types: Collection[EntityType],
        operations: Collection[OperationType],
    ) -> None:
        permissions_table = get_permissions_table()
        permission_inputs: list[dict[str, Any]] = []
        for entity_type in entity_types:
            for operation in operations:
                input = PermissionCreateInput(
                    permission_group_id=permission_group_id,
                    entity_type=entity_type,
                    operation=operation,
                )
                permission_inputs.append(input.to_dict())
        insert_if_data_exists(db_conn, permissions_table, permission_inputs)
