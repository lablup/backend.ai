"""migrate_artifact_registry_data_to_rbac

Revision ID: 6d850788c7c8
Revises: a4289ef5f0cd
Create Date: 2025-12-22 14:04:57.996593

"""

from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Row
from sqlalchemy.sql.expression import TableClause

from ai.backend.common.data.permission.types import GLOBAL_SCOPE_ID
from ai.backend.manager.data.permission.id import ObjectId, ScopeId, ScopeType
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
    RoleSource,
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_association_scopes_entities_table,
    get_permission_groups_table,
    get_permissions_table,
    get_roles_table,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    AssociationScopesEntitiesCreateInput,
    PermissionCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_if_data_exists,
    insert_skip_on_conflict,
)

# revision identifiers, used by Alembic.
revision = "6d850788c7c8"
down_revision = "a4289ef5f0cd"
branch_labels = None
depends_on = None


@dataclass
class PermissionGroupInfo:
    id: UUID
    role_source: RoleSource


class Tables:
    @classmethod
    def get_artifact_registries_table(cls) -> TableClause:
        table = sa.table(
            "artifact_registries",
            sa.column("id", GUID),
            extend_existing=True,
        )
        return table


class Migrator:
    @classmethod
    def _get_permission_group_ids_with_role_source(
        cls,
        db_conn: Connection,
        offset: int,
        limit: int,
    ) -> list[PermissionGroupInfo]:
        roles_table = get_roles_table()
        permission_groups_table = get_permission_groups_table()
        query = (
            sa.select(
                roles_table.c.source.label("role_source"),
                permission_groups_table.c.id.label("permission_group_id"),
            )
            .join(
                permission_groups_table,
                roles_table.c.id == permission_groups_table.c.role_id,
            )
            .order_by(permission_groups_table.c.id)
            .offset(offset)
            .limit(limit)
        )
        result = db_conn.execute(query)
        rows = result.all()
        return [PermissionGroupInfo(row.permission_group_id, row.role_source) for row in rows]

    @classmethod
    def _add_entity_typed_permission_to_permission_groups(
        cls,
        permission_group: PermissionGroupInfo,
    ) -> list[PermissionCreateInput]:
        match permission_group.role_source:
            case RoleSource.SYSTEM:
                operations = OperationType.owner_operations()
            case RoleSource.CUSTOM:
                operations = OperationType.member_operations()

        return [
            PermissionCreateInput(
                permission_group_id=permission_group.id,
                entity_type=EntityType.ARTIFACT_REGISTRY,
                operation=operation,
            )
            for operation in operations
        ]

    @classmethod
    def migrate_new_entity_type(
        cls,
        db_conn: Connection,
    ) -> None:
        permissions_table = get_permissions_table()
        offset = 0
        limit = 100

        while True:
            perm_groups = cls._get_permission_group_ids_with_role_source(db_conn, offset, limit)
            if not perm_groups:
                break

            offset += limit
            inputs: list[PermissionCreateInput] = []
            for perm_group in perm_groups:
                inputs.extend(
                    cls._add_entity_typed_permission_to_permission_groups(
                        perm_group,
                    )
                )
            insert_if_data_exists(
                db_conn,
                permissions_table,
                inputs,
            )

    @classmethod
    def query_entities(
        cls,
        db_conn: Connection,
    ) -> list[Row]:
        artifact_registries_table = Tables.get_artifact_registries_table()
        query = sa.select(
            artifact_registries_table.c.id.label("entity_id"),
        )
        result = db_conn.execute(query)
        rows = result.all()
        return rows

    @classmethod
    def associate_entity_to_scopes(
        cls,
        db_conn: Connection,
    ) -> None:
        association_scopes_entities_table = get_association_scopes_entities_table()
        artifact_registries_table = Tables.get_artifact_registries_table()
        offset = 0
        limit = 100

        while True:
            stmt = sa.select(artifact_registries_table.c.id).offset(offset).limit(limit)
            rows = db_conn.execute(stmt).all()
            if not rows:
                break
            offset += limit
            entity_inputs: list[AssociationScopesEntitiesCreateInput] = []

            for row in rows:
                entity_inputs.append(
                    AssociationScopesEntitiesCreateInput(
                        scope_id=ScopeId(
                            scope_type=ScopeType.GLOBAL,
                            scope_id=GLOBAL_SCOPE_ID,
                        ),
                        object_id=ObjectId(
                            entity_type=EntityType.ARTIFACT_REGISTRY.to_original(),
                            entity_id=str(row.id),
                        ),
                    )
                )
            insert_skip_on_conflict(
                db_conn,
                association_scopes_entities_table,
                [input.to_dict() for input in entity_inputs],
            )

    @classmethod
    def remove_entity_from_scopes(
        cls,
        db_conn: Connection,
    ) -> None:
        association_scopes_entities_table = get_association_scopes_entities_table()
        limit = 100

        while True:
            # Query records to delete
            stmt = (
                sa.select(association_scopes_entities_table.c.id)
                .where(
                    association_scopes_entities_table.c.entity_type == EntityType.ARTIFACT_REGISTRY
                )
                .limit(limit)
            )
            rows = db_conn.execute(stmt).all()
            if not rows:
                break

            # Delete the queried records
            ids = [row.id for row in rows]
            delete_stmt = association_scopes_entities_table.delete().where(
                association_scopes_entities_table.c.id.in_(ids)
            )
            db_conn.execute(delete_stmt)

    @classmethod
    def remove_entity_type_permissions(
        cls,
        db_conn: Connection,
    ) -> None:
        permissions_table = get_permissions_table()
        limit = 100

        while True:
            # Query permission IDs to delete
            stmt = (
                sa.select(permissions_table.c.id)
                .where(permissions_table.c.entity_type == EntityType.ARTIFACT_REGISTRY)
                .limit(limit)
            )
            rows = db_conn.execute(stmt).all()
            if not rows:
                break

            # Delete the queried permissions
            permission_ids = [row.id for row in rows]
            delete_stmt = permissions_table.delete().where(
                permissions_table.c.id.in_(permission_ids)
            )
            db_conn.execute(delete_stmt)


def upgrade() -> None:
    conn = op.get_bind()
    Migrator.migrate_new_entity_type(conn)
    Migrator.associate_entity_to_scopes(conn)


def downgrade() -> None:
    conn = op.get_bind()
    Migrator.remove_entity_from_scopes(conn)
    Migrator.remove_entity_type_permissions(conn)
