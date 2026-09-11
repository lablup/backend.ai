"""Types for role permission preset v2 DTOs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO

__all__ = (
    "RolePermissionPresetEntry",
    "RolePermissionPresetOrderField",
)


class RolePermissionPresetOrderField(StrEnum):
    """Fields available for ordering role permission preset entries."""

    ENTITY_TYPE = "entity_type"
    PERMISSION = "permission"
    CREATED_AT = "created_at"


class RolePermissionPresetEntry(BaseRequestModel):
    """A single (entity_type, permission) pair carried by a role preset."""

    entity_type: EntityType = Field(
        description="Entity type the permission applies to.",
    )
    permission: PermissionBitDTO = Field(description="The operation bit the entry grants.")
