"""How an operation the RBAC catalog lists is described."""

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType


def build_operation_description(
    operation: ActionOperationType,
    entity_type: EntityType,
) -> str:
    """Build a human-readable description from the operation and the entity it names."""
    entity = str(entity_type).replace("_", " ")
    match operation:
        case ActionOperationType.CREATE:
            return f"Create a new {entity}"
        case ActionOperationType.GET:
            return f"Get {entity} details"
        case ActionOperationType.SEARCH:
            return f"Search {entity} list"
        case ActionOperationType.LOOKUP:
            return f"Look up a {entity} by name"
        case ActionOperationType.UPDATE:
            return f"Update {entity}"
        case ActionOperationType.UPSERT:
            return f"Create or update {entity}"
        case ActionOperationType.DELETE:
            return f"Soft-delete {entity}"
        case ActionOperationType.RESTORE:
            return f"Restore a soft-deleted {entity}"
        case ActionOperationType.PURGE:
            return f"Hard-delete {entity}"
