"""migrate session data to RBAC

Revision ID: 22f6b779625e
Revises: 09206ac04fd3
Create Date: 2025-10-24 18:33:01.008923

"""

import uuid
from collections.abc import Collection
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import registry

from ai.backend.manager.data.permission.types import ScopeType
from ai.backend.manager.models.base import GUID, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
    RoleSource,
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_association_scopes_entities_table,
    get_permissions_table,
    get_roles_table,
)
from ai.backend.manager.models.rbac_models.migration.session import role_source_to_operation
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_if_data_exists,
    insert_skip_on_conflict,
)

# revision identifiers, used by Alembic.
revision = "22f6b779625e"
down_revision = "09206ac04fd3"
branch_labels = None
depends_on = None

mapper_registry = registry(metadata=metadata)


class Tables:
    @staticmethod
    def get_sessions_table() -> sa.Table:
        sessions_table = sa.Table(
            "sessions",
            mapper_registry.metadata,
            IDColumn("id"),
            sa.Column("user_uuid", GUID, nullable=False),
            sa.Column("group_id", GUID, nullable=False),
            sa.Column("domain_name", sa.String(64), nullable=False),
            extend_existing=True,
        )
        return sessions_table


class PermissionUpdator:
    @classmethod
    def _query_roles(
        cls, db_conn: Connection, offset: int, page_size: int, *, role_source: RoleSource
    ) -> list[Row]:
        roles_table = get_roles_table()
        query = (
            sa.select(roles_table)
            .where(roles_table.c.source == role_source)
            .offset(offset)
            .limit(page_size)
        )
        return db_conn.execute(query).all()

    @classmethod
    def _permission_inputs_to_permission_group(
        cls,
        permission_group_id: uuid.UUID,
        entity_type: EntityType,
        operations: Collection[OperationType],
    ) -> list[dict[str, Any]]:
        inputs: list[dict[str, Any]] = []
        for operation in operations:
            input = {
                "permission_group_id": permission_group_id,
                "entity_type": entity_type,
                "operation": str(operation),
            }
            inputs.append(input)
        return inputs

    @classmethod
    def add_permissions_to_system_sourced_roles(cls, db_conn: Connection) -> None:
        permissions_table = get_permissions_table()
        role_source = RoleSource.SYSTEM

        offset = 0
        page_size = 1000

        while True:
            roles = cls._query_roles(db_conn, offset, page_size, role_source=role_source)
            offset += page_size
            if not roles:
                break
            permission_inputs: list[dict[str, Any]] = []
            for row in roles:
                inputs = cls._permission_inputs_to_permission_group(
                    permission_group_id=row.permission_group_id,
                    entity_type=EntityType.SESSION,
                    operations=role_source_to_operation[role_source],
                )
                permission_inputs.extend(inputs)
            insert_if_data_exists(db_conn, permissions_table, permission_inputs)

    @classmethod
    def add_permissions_to_custom_sourced_roles(cls, db_conn: Connection) -> None:
        permissions_table = get_permissions_table()
        role_source = RoleSource.CUSTOM

        offset = 0
        page_size = 1000

        while True:
            roles = cls._query_roles(db_conn, offset, page_size, role_source=role_source)
            offset += page_size
            if not roles:
                break
            permission_inputs: list[dict[str, Any]] = []
            for row in roles:
                inputs = cls._permission_inputs_to_permission_group(
                    permission_group_id=row.permission_group_id,
                    entity_type=EntityType.SESSION,
                    operations=role_source_to_operation[role_source],
                )
                permission_inputs.extend(inputs)
            insert_if_data_exists(db_conn, permissions_table, permission_inputs)

    @classmethod
    def _query_sessions(cls, db_conn: Connection, offset: int, page_size: int) -> list[Row]:
        sessions_table = Tables.get_sessions_table()
        query = sa.select(sessions_table).offset(offset).limit(page_size)
        return db_conn.execute(query).all()

    @classmethod
    def map_session_to_scopes(cls, db_conn: Connection) -> None:
        association_scopes_entities_table = get_association_scopes_entities_table()

        offset = 0
        page_size = 1000

        while True:
            sessions = cls._query_sessions(db_conn, offset, page_size)
            offset += page_size
            if not sessions:
                break
            scope_entity_inputs: list[dict[str, Any]] = []
            for row in sessions:
                input = {
                    "entity_type": EntityType.SESSION,
                    "entity_id": str(row.id),
                    "scope_type": ScopeType.PROJECT,
                    "scope_id": str(row.group_id),
                }
                input = {
                    "entity_type": EntityType.SESSION,
                    "entity_id": str(row.id),
                    "scope_type": ScopeType.USER,
                    "scope_id": str(row.user_uuid),
                }
                scope_entity_inputs.append(input)
            insert_skip_on_conflict(db_conn, association_scopes_entities_table, scope_entity_inputs)


def upgrade() -> None:
    conn = op.get_bind()
    PermissionUpdator.add_permissions_to_system_sourced_roles(conn)
    PermissionUpdator.add_permissions_to_custom_sourced_roles(conn)


def downgrade() -> None:
    pass
