from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RBACElementType,
)
from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.repositories.base.creator import BulkCreatorError
from ai.backend.manager.repositories.base.purger import BulkPurgerError
from ai.backend.manager.repositories.base.updater import BulkUpdaterError

if TYPE_CHECKING:
    from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
        RolePermissionPresetRow,
    )
    from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow


@dataclass(frozen=True)
class RolePermissionPresetData:
    id: RolePermissionPresetID
    role_preset_id: RolePresetID
    entity_type: EntityType
    operation: OperationType
    created_at: datetime


@dataclass(frozen=True)
class RolePresetData:
    id: RolePresetID
    name: str
    scope_type: RBACElementType
    auto_assign: bool
    deleted: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RolePresetSearchResult:
    items: list[RolePresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class RolePresetBulkPurgeResult:
    successes: list[RolePresetData] = field(default_factory=list)
    failures: list[BulkPurgerError[RolePresetRow]] = field(default_factory=list)


@dataclass(frozen=True)
class RolePresetBulkUpdateResult:
    successes: list[RolePresetData] = field(default_factory=list)
    failures: list[BulkUpdaterError[RolePresetRow]] = field(default_factory=list)


@dataclass(frozen=True)
class RolePermissionPresetBulkAddResult:
    successes: list[RolePermissionPresetData] = field(default_factory=list)
    failures: list[BulkCreatorError[RolePermissionPresetRow]] = field(default_factory=list)


@dataclass(frozen=True)
class RolePermissionPresetBulkRemoveResult:
    successes: list[RolePermissionPresetData] = field(default_factory=list)
    failures: list[BulkPurgerError[RolePermissionPresetRow]] = field(default_factory=list)
