"""Valid RBAC entity-operation combinations.

This module defines which operations are valid for each entity type.
It is used for:
- Frontend UI filtering (which operations to show for a given entity type)
- Server-side validation (reject invalid operation-entity combinations)
"""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.data.permission.types import OperationType, RBACElementType

VALID_ENTITY_OPERATION_COMBINATIONS: Mapping[RBACElementType, frozenset[OperationType]] = {
    RBACElementType.VFOLDER: frozenset({
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
    OperationType.READ: "View and read the entity's details and metadata.",
    OperationType.UPDATE: "Modify the entity's properties and configuration.",
    OperationType.SOFT_DELETE: "Move the entity to trash (recoverable deletion).",
    OperationType.HARD_DELETE: "Permanently delete the entity (non-recoverable).",
    OperationType.GRANT_ALL: "Grant all permissions to other users, including the ability to grant permissions.",
    OperationType.GRANT_READ: "Grant read permissions to other users.",
    OperationType.GRANT_UPDATE: "Grant update permissions to other users.",
    OperationType.GRANT_SOFT_DELETE: "Grant soft-delete permissions to other users.",
    OperationType.GRANT_HARD_DELETE: "Grant hard-delete permissions to other users.",
}
