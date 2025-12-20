from collections.abc import Iterable
from uuid import UUID

from .entity.abc import AbstractEntityType
from .enums import EntityType, OperationType
from .types import AssociationScopesEntitiesCreateInput, PermissionCreateInput


class MigrationAdapter:
    """
    RBAC Migration Adapter.
    Provides methods to parse various migration input types.
    """

    def parse_entity_typed_permissions(
        self,
        permission_group_id: UUID,
        entity_type: EntityType,
        operations: Iterable[OperationType],
    ) -> list[PermissionCreateInput]:
        return [
            PermissionCreateInput(
                permission_group_id=permission_group_id,
                entity_type=entity_type,
                operation=operation,
            )
            for operation in operations
        ]

    def parse_association_scopes_entities(
        self, entity: AbstractEntityType
    ) -> list[AssociationScopesEntitiesCreateInput]:
        result: list[AssociationScopesEntitiesCreateInput] = []
        entity_id = entity.entity_id()
        for scope in entity.scopes():
            result.append(
                AssociationScopesEntitiesCreateInput(
                    scope_id=scope,
                    object_id=entity_id,
                )
            )
        return result
