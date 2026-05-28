"""Types for role permission preset v2 DTOs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.rbac.types import OperationTypeDTO, RBACElementTypeDTO

__all__ = (
    "RolePermissionPresetEntry",
    "RolePermissionPresetOrderField",
)


class RolePermissionPresetOrderField(StrEnum):
    """Fields available for ordering role permission preset entries."""

    ENTITY_TYPE = "entity_type"
    OPERATION = "operation"
    CREATED_AT = "created_at"


class RolePermissionPresetEntry(BaseRequestModel):
    """A single (entity_type, operation) pair carried by a role preset."""

    entity_type: RBACElementTypeDTO = Field(
        description="Entity type the permission applies to.",
    )
    operation: OperationTypeDTO = Field(description="Operation granted by the permission.")
