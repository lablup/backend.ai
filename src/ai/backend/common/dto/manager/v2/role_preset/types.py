"""Types for role preset v2 DTOs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import (
    EntityType,
    OperationTypeDTO,
    RBACElementTypeDTO,
)

__all__ = (
    "EntityType",
    "OperationTypeDTO",
    "OrderDirection",
    "RBACElementTypeDTO",
    "RolePermissionPresetEntry",
    "RolePresetOrderField",
)


class RolePresetOrderField(StrEnum):
    """Fields available for ordering role presets."""

    NAME = "name"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RolePermissionPresetEntry(BaseRequestModel):
    """A single (entity_type, operation) pair carried by a role preset."""

    entity_type: EntityType = Field(description="Entity type the permission applies to.")
    operation: OperationTypeDTO = Field(description="Operation granted by the permission.")
