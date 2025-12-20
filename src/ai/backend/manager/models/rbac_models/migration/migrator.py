import uuid
from dataclasses import dataclass
from typing import Generic

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from .adapter import MigrationAdapter
from .entity.abc import EntityQuerier, TEntity
from .enums import RoleSource
from .models import (
    get_association_scopes_entities_table,
    get_permission_groups_table,
    get_permissions_table,
    get_roles_table,
)
from .types import AssociationScopesEntitiesCreateInput
from .utils import insert_if_data_exists, insert_skip_on_conflict


@dataclass
class PermissionGroupInfo:
    id: uuid.UUID
    role_source: RoleSource


class EntityMigrator(Generic[TEntity]):
    """
    RBAC Entity Migrator.

    Handles entity-related data migrations for the RBAC system, including
    permission group queries, entity-typed permission creation, and
    entity-scope associations.

    This class provides utilities for migrating existing entities (VFolder,
    Session, etc.) to the RBAC permission model by:
    - Querying permission groups with their associated role sources
    - Adding entity-typed permissions to permission groups based on role type
    - Associating entities with their owning scopes

    Attributes:
        _adapter: MigrationAdapter instance for parsing migration input types.
        _db_conn: Database connection for executing queries and inserts.
        _entity_type: The entity type class providing entity type information and operations.
        _entity_querier: Entity querier for retrieving entity instances from the database.
    """

    def __init__(
        self,
        db_conn: Connection,
        entity_type: type[TEntity],
    ) -> None:
        self._adapter = MigrationAdapter()
        self._db_conn = db_conn
        self._entity_type = entity_type
        self._entity_querier = EntityQuerier(entity_type)

    def migrate_new_entity_type(
        self,
    ) -> None:
        """
        Migrate a new entity type into the RBAC permission system.

        When a new entity type is introduced to the system, this method ensures
        that all existing permission groups receive appropriate permission records
        for the new entity type. It iterates through all permission groups in the
        database and adds entity-typed permissions based on their role source
        (SYSTEM or CUSTOM).

        This is typically called during database migrations when adding support
        for a new resource type (e.g., VFolder, Session, Model Deployment) to the
        RBAC system.

        The entity type to migrate is specified during EntityMigrator initialization.
        """
        offset = 0
        limit = 100

        while True:
            perm_groups = self._get_permission_group_ids_with_role_source(offset, limit)
            if not perm_groups:
                break

            offset += limit
            for perm_group in perm_groups:
                self._add_entity_typed_permission_to_permission_groups(
                    perm_group,
                )

    def _get_permission_group_ids_with_role_source(
        self,
        offset: int,
        limit: int,
    ) -> list[PermissionGroupInfo]:
        """
        Query permission groups with their associated role sources.

        Args:
            db_conn: Database connection to execute the query.
            offset: Number of records to skip (for pagination).
            limit: Maximum number of records to return.

        Returns:
            List of PermissionGroupInfo containing permission group IDs and
            their associated role sources.
        """
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
        result = self._db_conn.execute(query)
        rows = result.all()
        return [PermissionGroupInfo(row.permission_group_id, row.role_source) for row in rows]

    def _add_entity_typed_permission_to_permission_groups(
        self,
        permission_group: PermissionGroupInfo,
    ) -> None:
        """
        Add entity-typed permissions to a permission group.

        Creates permission records in the permissions table for a specific entity
        type and permission group. The operations included depend on the role source:
        - SYSTEM roles: Get operations via entity_type.operations_in_system_role()
        - CUSTOM roles: Get operations via entity_type.operations_in_custom_role()

        Each permission record specifies an entity_type and operation (e.g., READ,
        UPDATE, DELETE) combination.

        Args:
            permission_group: Permission group information including ID and role source.
        """
        match permission_group.role_source:
            case RoleSource.SYSTEM:
                operations = self._entity_type.operations_in_system_role()
            case RoleSource.CUSTOM:
                operations = self._entity_type.operations_in_custom_role()

        permission_inputs = self._adapter.parse_entity_typed_permissions(
            permission_group_id=permission_group.id,
            entity_type=self._entity_type.entity_type(),
            operations=operations,
        )
        insert_if_data_exists(
            self._db_conn,
            get_permissions_table(),
            [input.to_dict() for input in permission_inputs],
        )

    def associate_entity_to_scopes(
        self,
    ) -> None:
        """
        Associate entities with their owning scopes.

        Queries entity instances from the database using the entity querier and
        creates records in the association_scopes_entities table to map each entity
        to its owning scopes. For example:
        - A VFolder may belong to a user scope or project scope
        - A Session may belong to a user scope
        - A Model Deployment may belong to a user scope

        The method processes entities in batches using pagination to handle large
        datasets efficiently. Uses ON CONFLICT DO NOTHING to safely handle duplicate
        entries.
        """
        association_scopes_entities_table = get_association_scopes_entities_table()

        for entities in self._entity_querier.query_entities(
            self._db_conn,
        ):
            entity_inputs: list[AssociationScopesEntitiesCreateInput] = []
            for entity in entities:
                entity_inputs.extend(self._adapter.parse_association_scopes_entities(entity))
            insert_skip_on_conflict(
                self._db_conn,
                association_scopes_entities_table,
                [input.to_dict() for input in entity_inputs],
            )
