"""Types for role preset v2 DTOs."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import (
    EntityType,
    OperationTypeDTO,
    RBACElementTypeDTO,
)
from ai.backend.common.identifier.role_preset import RolePresetID

__all__ = (
    "EntityType",
    "OperationTypeDTO",
    "OrderDirection",
    "RBACElementTypeDTO",
    "RolePermissionPresetEntry",
    "RolePermissionPresetInfo",
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


class RolePermissionPresetInfo(BaseResponseModel):
    """Response representation of one stored permission entry under a role preset."""

    id: UUID = Field(description="UUID of the permission entry row.")
    role_preset_id: RolePresetID = Field(description="UUID of the parent role preset.")
    entity_type: EntityType = Field(description="Entity type the permission applies to.")
    operation: OperationTypeDTO = Field(description="Operation granted by the permission.")
    created_at: datetime = Field(description="Creation timestamp.")
