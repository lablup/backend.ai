"""Valid RBAC entity-operation combinations based on BEP-1048.

This module is the single source of truth for which operations are valid
for each entity type. It is used for:
- Frontend UI filtering (which operations to show for a given entity)
- Server-side validation (reject invalid combinations)
- Permission system configuration
"""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.data.permission.types import OperationType, RBACElementType

VALID_ENTITY_OPERATION_COMBINATIONS: Mapping[RBACElementType, frozenset[OperationType]] = {
    RBACElementType.MODEL_DEPLOYMENT: frozenset({
        OperationType.CREATE,
        OperationType.READ,
        OperationType.UPDATE,
        OperationType.SOFT_DELETE,
        OperationType.HARD_DELETE,
        OperationType.GRANT_ALL,
        OperationType.GRANT_READ,
        OperationType.GRANT_UPDATE,
        OperationType.GRANT_SOFT_DELETE,
        OperationType.GRANT_HARD_DELETE,
    }),
}

OPERATION_DESCRIPTIONS: Mapping[OperationType, str] = {
    OperationType.CREATE: "Create a new instance of the entity.",
    OperationType.READ: "View the entity and its details.",
    OperationType.UPDATE: "Modify the entity's properties or configuration.",
    OperationType.SOFT_DELETE: "Deactivate or mark the entity as deleted without permanent removal.",
    OperationType.HARD_DELETE: "Permanently remove the entity from the system.",
    OperationType.GRANT_ALL: "Grant all permissions on the entity to other users or roles, including the ability to grant permissions.",
    OperationType.GRANT_READ: "Grant read permission on the entity to other users or roles.",
    OperationType.GRANT_UPDATE: "Grant update permission on the entity to other users or roles.",
    OperationType.GRANT_SOFT_DELETE: "Grant soft-delete permission on the entity to other users or roles.",
    OperationType.GRANT_HARD_DELETE: "Grant hard-delete permission on the entity to other users or roles.",
}
