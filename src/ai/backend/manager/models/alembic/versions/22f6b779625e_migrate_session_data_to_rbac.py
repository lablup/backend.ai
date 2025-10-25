"""migrate session data to RBAC

Revision ID: 22f6b779625e
Revises: 09206ac04fd3
Create Date: 2025-10-24 18:33:01.008923

"""

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
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_association_scopes_entities_table,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    EntityAddUtil,
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
                project_mapping = {
                    "entity_type": EntityType.SESSION,
                    "entity_id": str(row.id),
                    "scope_type": ScopeType.PROJECT,
                    "scope_id": str(row.group_id),
                }
                scope_entity_inputs.append(project_mapping)
                user_mapping = {
                    "entity_type": EntityType.SESSION,
                    "entity_id": str(row.id),
                    "scope_type": ScopeType.USER,
                    "scope_id": str(row.user_uuid),
                }
                scope_entity_inputs.append(user_mapping)
            insert_skip_on_conflict(db_conn, association_scopes_entities_table, scope_entity_inputs)


def upgrade() -> None:
    conn = op.get_bind()
    EntityAddUtil.add_permissions_to_system_sourced_roles(
        conn,
        entity_type=EntityType.SESSION,
        operations=OperationType.owner_operations(),
    )
    EntityAddUtil.add_permissions_to_custom_sourced_roles(
        conn,
        entity_type=EntityType.SESSION,
        operations=OperationType.member_operations(),
    )
    PermissionUpdator.map_session_to_scopes(conn)


def downgrade() -> None:
    pass
